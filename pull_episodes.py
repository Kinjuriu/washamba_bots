#!/usr/bin/env python3
"""
pull_episodes.py  -  Washamba Bots' own Kaggriculture replay puller.

Downloads every public ladder game (replay) played by a chosen set of
leaderboard agents, straight from Kaggle's own episode API, using your
existing signed-in Chrome session. No dependency on anyone else's scraper,
so we know exactly what it grabs: all games for the submissions we name,
nothing hidden, nothing sampled.

How it works (confirmed live on 21 Sep 2026):
  1. ListEpisodes  -> POST https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes
        body {"submissionId": <id>}  ->  {"episodes":[...], "teams":[...], "submissions":[...]}
        Each episode row carries both agents' submissionId, teamId, seat index,
        final reward (bank) and the rating delta. One call returns a submission's
        whole game history (DSM returned 109 in one shot); we still follow a
        nextPageToken if Kaggle ever adds one.
  2. Replay       -> GET https://www.kaggle.com/competitions/episodes/<episodeId>/replay.json
        The full kaggle_environments replay: 720 steps, 2 agents per step,
        each step = {action, observation, reward, status}. ~34 MB raw each,
        so we store them gzipped (drops to a few MB) and never re-download.

Auth: these are the site's internal endpoints, so they need your Kaggle login,
not an API key. The script reuses your Chrome cookies automatically
(browser_cookie3). If that can't read them, see the COOKIE FALLBACK note below.
Never paste cookie values into this script, a chat, a prompt, or a committed
file of any kind (including .env) - the only accepted place for a manual
cookie is the KAGGLE_COOKIE environment variable, set yourself, in your own
shell, for your own local run.

STORAGE: --out is required and is checked, before any network request, to
be outside this Git repo and outside every folder macOS/iCloud could sync
(Desktop, Documents, iCloud Drive). A run that resolves inside any of those
refuses to start. The recommended location:
    ~/KagricultureLocalData/episodes/
        manifest.csv          one row per (episode, our target player) with opponents,
                              seats, banks, ratings, timestamps  -> analyse without
                              opening a single multi-MB replay file
        replays/<id>.json.gz  the full gzipped replay per unique episode
        teams.json            teamName -> teamId / active submissionId map, for reference
        logs/                 malformed-episode and failed-download logs

Run:
    pip install requests browser_cookie3
    python pull_episodes.py --out ~/KagricultureLocalData/episodes --manifest-only
    python pull_episodes.py --out ~/KagricultureLocalData/episodes
    python pull_episodes.py --out ~/KagricultureLocalData/episodes --top9       # + the other 4 known teams
    python pull_episodes.py --out ~/KagricultureLocalData/episodes --max-games 0  # no per-player cap

NOTE ON manifest.csv: it is one row per (episode, target player), not one row
per episode. When two of our target players played each other, that single
episode produces two manifest rows (one from each player's perspective) but
the replay itself is still only downloaded/stored once, keyed by episode id.
"""

import argparse
import csv
import gzip
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Targets. These are the CURRENT active leaderboard submissions, captured
# 21 Sep 2026 16:4x EAT. THIS IS A DATED SNAPSHOT, NOT A LIVE LOOKUP - a
# team's active submission changes whenever they push a new agent, so if a
# run comes back with few/old games, refresh these ids by hand (open the
# team on the leaderboard; the URL's submissionId= is the new one).
# ---------------------------------------------------------------------------
TOP5 = {
    "DSM":                  56409623,
    "Majkel1337":           56407295,
    "ymg_aq":               56416487,
    "Unknown Mother-Goose": 56401905,
    "Vadim Vasilenko":      56396983,
}
# 4 more captured teams, bringing the known total to 9 of the top 10.
# KawattaTaido's submission id was not reachable from DSM's game list at
# capture time and is still missing - add it here once known.
EXTRA_TEAMS = {
    "THIRD FARM CLUB":      56395336,
    "SpaTaro":              56384319,
    "QQ":                   56327925,
    "Otter Vibe":           56353982,
}

BASE = "https://www.kaggle.com"
LIST_URL = BASE + "/api/i/competitions.EpisodeService/ListEpisodes"
REPLAY_URL = BASE + "/competitions/episodes/{eid}/replay.json"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36")

CONNECT_TIMEOUT = 10
READ_TIMEOUT = 60
MAX_RETRIES = 5


# ---------------------------------------------------------------------------
# Local-storage safety: never let this land somewhere iCloud will sync.
# ---------------------------------------------------------------------------
class OutsideAllowedLocation(Exception):
    """Raised when --out resolves somewhere we refuse to write."""


def find_repo_root(start):
    cur = start
    for _ in range(12):
        if (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return start


def _is_inside(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_out_dir(out_arg, home=None, repo_root=None):
    """Resolve --out to an absolute path and refuse it if it's anywhere
    iCloud could sync (Desktop, Documents, iCloud Drive) or inside this
    Git repo. `home`/`repo_root` are overridable for tests."""
    out = Path(out_arg).expanduser().resolve()
    home = (home or Path.home()).resolve()
    repo_root = (repo_root or find_repo_root(Path(__file__).resolve().parent)).resolve()

    forbidden = {
        "the washamba_bots Git repository": repo_root,
        "your Desktop (iCloud may sync this)": (home / "Desktop").resolve(),
        "your Documents folder (iCloud may sync this)": (home / "Documents").resolve(),
        "iCloud Drive": (home / "Library" / "Mobile Documents").resolve(),
    }
    for label, root in forbidden.items():
        if root.exists() and _is_inside(out, root):
            raise OutsideAllowedLocation(
                f"Refusing to write inside {label}: {root}\n"
                f"Resolved --out path: {out}\n"
                "Pick a location outside Desktop, Documents, iCloud Drive and this "
                "repo, e.g. --out ~/KagricultureLocalData/episodes"
            )
    return out


def normalize_id(value):
    """Kaggle's API mixes numeric and string ids across payloads. Normalize
    to int when possible so a str/int mismatch never breaks an equality
    check (e.g. submissionId 56409623 vs "56409623")."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return str(value)


def log_warning(logs_dir, filename, message):
    logs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(logs_dir / filename, "a", encoding="utf-8") as fh:
        fh.write(f"{ts} {message}\n")
    print(f"    WARNING: {message}")


# ---------------------------------------------------------------------------
# Auth: reuse the Chrome session you already have open on kaggle.com.
# ---------------------------------------------------------------------------
def build_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "Accept": "application/json",
        "Origin": BASE,
        "Referer": BASE + "/competitions/kaggriculture/leaderboard",
    })

    cookie_header = os.environ.get("KAGGLE_COOKIE", "").strip()
    xsrf = None

    if cookie_header:
        # COOKIE FALLBACK: set the whole Cookie: header value in the
        # KAGGLE_COOKIE env var yourself, in your own shell. Get it from
        # Chrome DevTools -> Network -> any kaggle.com request -> Request
        # Headers -> Cookie. Never paste it into a chat, a prompt, or any
        # file that could end up committed.
        s.headers["Cookie"] = cookie_header
        for part in cookie_header.split(";"):
            if part.strip().startswith("XSRF-TOKEN="):
                xsrf = requests.utils.unquote(part.strip()[len("XSRF-TOKEN="):])
    else:
        try:
            import browser_cookie3
        except ImportError:
            sys.exit(
                "Need cookies to talk to Kaggle. Either:\n"
                "  pip install browser_cookie3   (reuses your Chrome login automatically)\n"
                "or set the KAGGLE_COOKIE env var yourself, in your own shell, to the\n"
                "Cookie header from a logged-in kaggle.com request. Never paste a cookie\n"
                "value into a chat, a prompt, or any file you might commit."
            )
        cj = None
        for loader in (getattr(browser_cookie3, "chrome", None),
                       getattr(browser_cookie3, "load", None)):
            if loader is None:
                continue
            try:
                cj = loader(domain_name="kaggle.com")
                if cj and any(c.name == "XSRF-TOKEN" for c in cj):
                    break
            except Exception:
                cj = None
        if not cj:
            sys.exit(
                "Could not read Kaggle cookies from Chrome. On macOS this is usually a\n"
                "Keychain permission prompt - if one appeared, click 'Always Allow' and\n"
                "re-run. Otherwise, make sure you are logged in to kaggle.com in Chrome.\n"
                "As a last resort, set KAGGLE_COOKIE yourself in your own shell (see\n"
                "build_session() for how) - never paste cookies into this chat, a\n"
                "prompt, or a file you might commit."
            )
        s.cookies.update(cj)
        for c in cj:
            if c.name == "XSRF-TOKEN":
                xsrf = requests.utils.unquote(c.value)

    if not xsrf:
        sys.exit("No XSRF-TOKEN cookie found. Open kaggle.com in Chrome, log in, "
                 "reload the leaderboard once, then re-run.")
    s.headers["X-XSRF-TOKEN"] = xsrf
    return s


# ---------------------------------------------------------------------------
# Shared request helper: timeouts, retries, exponential backoff.
# ---------------------------------------------------------------------------
def _request(session, method, url, tries=MAX_RETRIES, **kwargs):
    kwargs.setdefault("timeout", (CONNECT_TIMEOUT, READ_TIMEOUT))
    last_exc = None
    for attempt in range(tries):
        try:
            r = session.request(method, url, **kwargs)
        except requests.exceptions.RequestException as e:
            last_exc = e
            wait = 2 ** attempt
            print(f"    {url.split('/')[-1]}: {e.__class__.__name__}, retry in {wait}s")
            time.sleep(wait)
            continue
        if r.status_code == 200 or r.status_code not in (429, 500, 502, 503, 504):
            return r
        wait = 2 ** attempt
        print(f"    {url.split('/')[-1]} -> {r.status_code}, retry in {wait}s")
        time.sleep(wait)
    if last_exc:
        raise RuntimeError(f"{url} failed after {tries} tries: {last_exc}")
    raise RuntimeError(f"{url} failed after {tries} tries")


def _post_json(session, url, body, tries=MAX_RETRIES):
    r = _request(session, "POST", url, tries=tries,
                 data=json.dumps(body), headers={"Content-Type": "application/json"})
    if r.status_code != 200:
        raise RuntimeError(f"{url} -> {r.status_code}: {r.text[:200]}")
    ctype = r.headers.get("Content-Type", "")
    if "json" not in ctype.lower():
        raise RuntimeError(
            f"{url} returned '{ctype or 'unknown'}' instead of JSON - likely a login "
            "page, meaning your Kaggle session has expired. Reload kaggle.com in "
            "Chrome while logged in, then re-run."
        )
    try:
        return r.json()
    except ValueError as e:
        raise RuntimeError(f"{url} returned 200 but invalid JSON: {e}")


# ---------------------------------------------------------------------------
# Enumerate a submission's whole game history.
# ---------------------------------------------------------------------------
def list_episodes(session, submission_id):
    episodes, teams = [], {}
    body = {"submissionId": submission_id}
    while True:
        data = _post_json(session, LIST_URL, body)
        episodes.extend(data.get("episodes", []))
        for t in data.get("teams", []):
            teams[normalize_id(t.get("id"))] = {
                "teamName": t.get("teamName"),
                "activeSubmissionId": t.get("publicLeaderboardSubmissionId"),
            }
        token = data.get("nextPageToken")
        if not token:
            break
        body = {"submissionId": submission_id, "pageToken": token}
    return episodes, teams


def iso(ts):
    return (ts or "").replace("T", " ").replace("Z", "")[:19]


def build_manifest_rows(name, sub_id, episodes, all_teams, logs_dir):
    """Turn one target player's raw episode list into manifest rows. Skips
    (and logs, rather than silently defaulting to seat 0) any episode where
    the target agent - or its opponent - can't be found, so a malformed
    record never pollutes the manifest with a fabricated seat."""
    sub_id_norm = normalize_id(sub_id)
    rows = []
    for ep in episodes:
        eid = ep.get("id")
        if eid is None:
            log_warning(logs_dir, "malformed_episodes.log",
                        f"[{name}] episode with no 'id' field, skipped")
            continue

        agents = ep.get("agents", [])
        me = next((a for a in agents
                   if normalize_id(a.get("submissionId")) == sub_id_norm), None)
        if me is None:
            log_warning(logs_dir, "malformed_episodes.log",
                        f"[{name}] episode {eid}: target submission {sub_id} not "
                        "found among its agents, skipped (not assigned seat 0)")
            continue
        opp = next((a for a in agents
                    if normalize_id(a.get("submissionId")) != sub_id_norm), None)
        if opp is None:
            log_warning(logs_dir, "malformed_episodes.log",
                        f"[{name}] episode {eid}: no opponent agent found, skipped")
            continue

        # Kaggle's ListEpisodes payload is proto3-JSON: a field holding its
        # type's zero value is omitted entirely rather than sent as 0.
        # Verified live - no agent ever carries an explicit "index": 0, only
        # an absent key (seat 0) or an explicit 1. So `index` absent on an
        # agent we've already confirmed exists (`me`/`opp` is not None) is
        # the correct, expected encoding of seat 0 - not missing data, and
        # not the seat-0-on-a-missing-agent bug guarded against above.
        opp_team = all_teams.get(normalize_id(opp.get("teamId")))
        rows.append({
            "player": name,
            "player_submission": sub_id,
            "episode_id": eid,
            "end_time": iso(ep.get("endTime")),
            "state": ep.get("state"),
            "player_seat": me.get("index", 0),
            "player_bank": me.get("reward"),
            "player_rating_before": me.get("initialScore"),
            "player_rating_after": me.get("updatedScore"),
            "opponent_name": (opp_team or {}).get("teamName"),
            "opponent_team": opp.get("teamId"),
            "opponent_submission": opp.get("submissionId"),
            "opponent_seat": opp.get("index", 0),
            "opponent_bank": opp.get("reward"),
            "won": (None if me.get("reward") is None or opp.get("reward") is None
                    else int(me["reward"] > opp["reward"])),
        })
    return rows


# ---------------------------------------------------------------------------
# Replay structural validation - never trust a 200 or a cached file blindly.
# ---------------------------------------------------------------------------
def validate_replay_structure(data):
    """Return (ok, reason). Checks the shape we actually rely on downstream:
    a non-empty steps list, a configuration block, and rewards on the final
    step - without over-fitting to fields we don't use."""
    if not isinstance(data, dict):
        return False, "top-level JSON is not an object"
    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        return False, "missing or empty 'steps'"
    if not isinstance(data.get("configuration"), dict):
        return False, "missing 'configuration'"
    last_step = steps[-1]
    if not isinstance(last_step, list) or not last_step:
        return False, "final step has no agent entries (no rewards)"
    rewards = [a.get("reward") for a in last_step if isinstance(a, dict)]
    if not rewards or all(r is None for r in rewards):
        return False, "final step has no rewards"
    return True, ""


# ---------------------------------------------------------------------------
# Download one replay: stream to a .part file, validate, gzip, validate the
# gzip, then atomically rename. Nothing at the final path is ever partial
# or unvalidated - and a cached file is re-validated before being trusted.
# ---------------------------------------------------------------------------
def download_replay(session, eid, replay_dir, logs_dir, tries=MAX_RETRIES):
    final_path = replay_dir / f"{eid}.json.gz"

    if final_path.exists() and final_path.stat().st_size > 0:
        try:
            with gzip.open(final_path, "rt", encoding="utf-8") as fh:
                data = json.load(fh)
            ok, reason = validate_replay_structure(data)
            if ok:
                return "cached"
            log_warning(logs_dir, "download_failures.log",
                        f"episode {eid}: cached file failed validation ({reason}), re-downloading")
        except Exception as e:
            log_warning(logs_dir, "download_failures.log",
                        f"episode {eid}: cached file unreadable ({e}), re-downloading")
        final_path.unlink(missing_ok=True)

    url = REPLAY_URL.format(eid=eid)
    raw_tmp = replay_dir / f".{eid}.json.part"
    gz_tmp = replay_dir / f".{eid}.json.gz.part.{uuid.uuid4().hex[:8]}"
    last_reason = "unknown error"

    try:
        for attempt in range(tries):
            raw_tmp.unlink(missing_ok=True)
            try:
                with session.get(url, stream=True,
                                  timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)) as r:
                    if r.status_code != 200:
                        if r.status_code in (429, 500, 502, 503, 504):
                            wait = 2 ** attempt
                            print(f"    replay {eid} -> {r.status_code}, retry in {wait}s")
                            time.sleep(wait)
                            continue
                        last_reason = f"HTTP {r.status_code}"
                        break
                    ctype = r.headers.get("Content-Type", "")
                    if "json" not in ctype.lower():
                        last_reason = (f"200 but content-type '{ctype or 'unknown'}' "
                                        "(likely a login page - session may have expired)")
                        break
                    with open(raw_tmp, "wb") as fh:
                        for chunk in r.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                fh.write(chunk)
            except requests.exceptions.RequestException as e:
                last_reason = f"{e.__class__.__name__}: {e}"
                wait = 2 ** attempt
                print(f"    replay {eid}: {last_reason}, retry in {wait}s")
                time.sleep(wait)
                continue

            try:
                with open(raw_tmp, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                last_reason = f"response was not valid JSON ({e}) - likely an HTML login/error page"
                break

            ok, reason = validate_replay_structure(data)
            if not ok:
                last_reason = f"replay failed structural validation ({reason})"
                break

            size_mb = raw_tmp.stat().st_size / 1e6
            with open(raw_tmp, "rb") as src, gzip.open(gz_tmp, "wb") as dst:
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    dst.write(chunk)

            try:
                with gzip.open(gz_tmp, "rt", encoding="utf-8") as fh:
                    json.load(fh)
            except Exception as e:
                last_reason = f"gzip validation failed after compression ({e})"
                break

            os.replace(gz_tmp, final_path)  # atomic - only now is it a real cached file
            return f"{size_mb:.1f}MB"

        log_warning(logs_dir, "download_failures.log", f"episode {eid}: {last_reason}")
        return f"ERR {last_reason}"
    finally:
        raw_tmp.unlink(missing_ok=True)
        gz_tmp.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(
        description="Pull Kaggriculture ladder replays for the top players.")
    ap.add_argument("--out", required=True,
                    help="Local output directory. Required, and checked before any "
                         "network request - must be OUTSIDE Desktop, Documents, iCloud "
                         "Drive and this repo. Recommended: ~/KagricultureLocalData/episodes")
    ap.add_argument("--top9", action="store_true",
                    help="Also include the 4 other known teams (9 of the top 10 "
                         "captured; KawattaTaido's submission id is not yet known).")
    ap.add_argument("--max-games", type=int, default=60,
                    help="newest N games per player (0 = all). Default 60.")
    ap.add_argument("--manifest-only", action="store_true",
                    help="write the metadata CSV but do not download replays")
    ap.add_argument("--sleep", type=float, default=0.5,
                    help="seconds to pause between replay downloads (be polite)")
    args = ap.parse_args()

    try:
        out_dir = resolve_out_dir(args.out)
    except OutsideAllowedLocation as e:
        sys.exit(str(e))

    print(f"Output directory (resolved): {out_dir}")
    print("Verified outside the washamba_bots repo, Desktop, Documents and iCloud Drive.\n")

    replay_dir = out_dir / "replays"
    logs_dir = out_dir / "logs"
    out_dir.mkdir(parents=True, exist_ok=True)
    replay_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    targets = dict(TOP5)
    if args.top9:
        targets.update(EXTRA_TEAMS)

    session = build_session()
    print(f"Authenticated. Targets: {', '.join(targets)}")

    all_teams = {}
    manifest_rows = []          # one row per (episode, target player)
    all_eids = set()            # unique episode ids across every target
    eid_players = {}            # eid -> set of target player names, for the dup note

    for name, sub_id in targets.items():
        print(f"\n[{name}] submission {sub_id}: listing games ...")
        try:
            episodes, teams = list_episodes(session, sub_id)
        except Exception as e:
            print(f"    could not list episodes: {e}")
            continue
        all_teams.update(teams)

        episodes.sort(key=lambda e: e.get("endTime", ""), reverse=True)
        if args.max_games and args.max_games > 0:
            episodes = episodes[:args.max_games]
        print(f"    {len(episodes)} games (after cap)")

        rows = build_manifest_rows(name, sub_id, episodes, all_teams, logs_dir)
        for row in rows:
            eid = row["episode_id"]
            all_eids.add(eid)
            eid_players.setdefault(eid, set()).add(name)
        manifest_rows.extend(rows)

    with open(out_dir / "teams.json", "w", encoding="utf-8") as fh:
        json.dump(all_teams, fh, indent=2)

    manifest_path = out_dir / "manifest.csv"
    cols = ["player", "player_submission", "episode_id", "end_time", "state",
            "player_seat", "player_bank", "player_rating_before", "player_rating_after",
            "opponent_name", "opponent_team", "opponent_submission",
            "opponent_seat", "opponent_bank", "won"]
    with open(manifest_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(manifest_rows)

    unique_eids = sorted(all_eids)
    dup_eids = [eid for eid, players in eid_players.items() if len(players) > 1]
    print(f"\nManifest: {len(manifest_rows)} rows across {len(unique_eids)} unique games "
          f"-> {manifest_path}")
    if dup_eids:
        print(f"{len(dup_eids)} of those games have two manifest rows (two target "
              "players faced each other) - the replay is still downloaded once, "
              f"by episode id: {dup_eids[:10]}{' ...' if len(dup_eids) > 10 else ''}")

    if args.manifest_only:
        print("manifest-only: skipping replay downloads.")
        return

    print(f"\nDownloading {len(unique_eids)} unique replays (gzipped) -> {replay_dir}")
    done = 0
    for i, eid in enumerate(unique_eids, 1):
        status = download_replay(session, eid, replay_dir, logs_dir)
        done += 1 if status not in ("cached",) and not status.startswith("ERR") else 0
        print(f"  [{i}/{len(unique_eids)}] {eid}: {status}")
        if not status.startswith("ERR") and status != "cached":
            time.sleep(args.sleep)
    print(f"\nDone. New downloads: {done}. "
          f"Everything in {out_dir}. Re-runs skip files already present and valid.")


if __name__ == "__main__":
    main()
