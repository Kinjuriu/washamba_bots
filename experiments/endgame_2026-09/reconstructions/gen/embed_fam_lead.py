"""Reusable: load router_fam_lead.py, rename its top-level identifiers with
an _FL_ suffix (leaving the huge blob payload line untouched) so it can be
embedded alongside base_backbone.py's own names without collision, and
rename its `agent` entrypoint to `_agent_fam_lead_floor`.
"""
import re

REPO = "/Users/stephanengugi/Desktop/washamba_bots"
FAM_LEAD = f"{REPO}/agents/router_fam_lead.py"

FL_IDENTIFIERS = [
    "_TAPES_DATA", "_TAPES", "FIRST_ROUTES", "SECOND_ROUTES", "SAFE_KEYS",
    "HANDOVER_AT_72", "_get", "_pass", "_which", "LEAD_K", "LEAD_START",
    "LEAD_SKIP", "_lead_used", "_advance_sells", "agent",
]
BLOB_LINE_THRESHOLD = 1000


def load_fam_lead_renamed():
    with open(FAM_LEAD) as f:
        src = f.read()
    lines = src.split("\n")
    out = []
    for line in lines:
        if len(line) > BLOB_LINE_THRESHOLD:
            if line.startswith("_TAPES_DATA = "):
                line = "_TAPES_DATA_FL = " + line[len("_TAPES_DATA = "):]
            out.append(line)
            continue
        new_line = line
        for ident in FL_IDENTIFIERS:
            new_line = re.sub(r"\b%s\b" % re.escape(ident), ident + "_FL", new_line)
        out.append(new_line)
    src = "\n".join(out)
    assert "def agent_FL(observation, configuration=None):" in src
    src = src.replace("def agent_FL(", "def _agent_fam_lead_floor(", 1)
    return src
