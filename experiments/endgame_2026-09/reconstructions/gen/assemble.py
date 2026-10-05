"""Assemble one recon_*.py agent: patched base_backbone core + embedded
router_fam_lead floor + embedded macro-route blob + executor template.

Usage: python3 assemble.py <routes_json> <player_name> <out_path> <module_tag> <use_recon_flag>
"""
import base64, json, sys, zlib

sys.path.insert(0, "/Users/stephanengugi/KagricultureLocalData/reconstructions/gen")
from build_recon import load_base_backbone_patched
from embed_fam_lead import load_fam_lead_renamed

DEFAULT_TEMPLATE = "/Users/stephanengugi/KagricultureLocalData/reconstructions/gen/executor_template.py"


def embed_routes_blob(routes, var_name):
    raw = json.dumps(routes).encode("utf-8")
    blob = base64.b85encode(zlib.compress(raw, 9)).decode("ascii")
    return (
        f"{var_name}_DATA = '{blob}'\n"
        f"{var_name} = __import__('json').loads("
        f"__import__('zlib').decompress(__import__('base64').b85decode({var_name}_DATA)))\n"
    )


def main():
    routes_path, player_name, out_path, module_tag, use_recon = sys.argv[1:6]
    template_path = sys.argv[6] if len(sys.argv) > 6 else DEFAULT_TEMPLATE
    with open(routes_path) as f:
        routes = json.load(f)

    base_src = load_base_backbone_patched()
    fam_lead_src = load_fam_lead_renamed()
    blob_src = embed_routes_blob(routes, "_ROUTES")

    with open(template_path) as f:
        exec_src = f.read().replace("{PLAYER}", player_name)

    header = (
        f'"""\n'
        f"recon_{module_tag.lower()} - a route agent reconstructed from {player_name}'s own\n"
        f"winning ladder replays (public Kaggle episode/replay API, same method as\n"
        f"router_yhay.py/V56/docs/REPLAY_ANALYSIS.md), executed through\n"
        f"base_backbone.py's own legality/movement/sanitizing layer.\n"
        f"\n"
        f"See the MACRO ROUTE EXECUTOR section near the bottom for the method and\n"
        f"the floor-fallback design. Read-only against the local replay corpus at\n"
        f"analysis time (~/KagricultureLocalData/episodes) - nothing at inference\n"
        f'time; the macro routes below are embedded, not read from disk.\n"""\n\n'
        f"USE_RECON = {use_recon}\n\n"
    )

    with open(out_path, "w") as f:
        f.write(header)
        f.write(base_src)
        f.write("\n\n# " + "=" * 71 + "\n")
        f.write("# FLOOR: router_fam_lead.py, embedded unmodified except identifier\n")
        f.write("# renames (_FL suffix) to avoid colliding with base_backbone's names\n")
        f.write("# above, and its `agent` renamed to `_agent_fam_lead_floor`.\n")
        f.write("# " + "=" * 71 + "\n\n")
        f.write(fam_lead_src)
        f.write("\n\n# " + "=" * 71 + "\n")
        f.write(f"# Embedded macro routes reconstructed from {player_name}'s wins,\n")
        f.write("# one per turn-72 opening shop key, plus a shared OPENING route.\n")
        f.write("# " + "=" * 71 + "\n\n")
        f.write(blob_src)
        f.write("\n")
        f.write(exec_src)

    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
