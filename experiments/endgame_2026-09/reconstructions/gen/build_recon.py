"""Generate a recon_*.py agent: base_backbone.py's helper/legality layer,
patched to accept a macro-plan-driven crop/animal picker, plus the macro
executor and an embedded route blob for one leader.

Usage: python3 build_recon.py <routes_json> <opening_key_or_ALL> <out_path> <module_tag>
"""
import base64, json, sys, zlib

REPO = "/Users/stephanengugi/Desktop/washamba_bots"
BASE_BACKBONE = f"{REPO}/agents/base_backbone.py"


def load_base_backbone_patched():
    with open(BASE_BACKBONE) as f:
        src = f.read()

    old_sig = (
        "def choose_unit_action(\n"
        "    state, ux, uy, unit_idx, claimed=None, pending_builds=None, feed_claimed=None,\n"
        "    plant_budget=None, wheat_budget=None,\n"
        "):"
    )
    new_sig = (
        "def choose_unit_action(\n"
        "    state, ux, uy, unit_idx, claimed=None, pending_builds=None, feed_claimed=None,\n"
        "    plant_budget=None, wheat_budget=None, crop_picker=None, animal_picker=None,\n"
        "):"
    )
    assert src.count(old_sig) == 1, "choose_unit_action signature not found"
    src = src.replace(old_sig, new_sig, 1)

    old_block = (
        "    if tile is None:\n"
        "        animal_to_build = choose_animal_to_build(\n"
        "            farm, private, board_size, day, pending_builds[0], ux, uy\n"
        "        )\n"
        "        if animal_to_build:\n"
        "            pending_builds[0] += 1\n"
        "            structure = ANIMALS[animal_to_build][\"structure\"]\n"
        "            return act_here([f\"BUILD_{structure}\"])\n"
        "        crop = choose_crop(\n"
        "            farm,\n"
        "            state[\"market_state\"],\n"
        "            private,\n"
        "            day,\n"
        "            unlocked_shops=state.get(\"unlocked_shops\", ()),\n"
        "            start_step=state.get(\"step\"),\n"
        "            opponent_pipeline=state.get(\"opponent_pipeline\"),\n"
        "        )\n"
        "        if crop and plant_budget.get(crop, 0) <= 0:\n"
        "            # Top pick can't be planted this turn (zero held seed, chosen\n"
        "            # via can_afford) - fall back to the best-scoring crop we\n"
        "            # actually hold seed for, rather than wasting the turn. See\n"
        "            # choose_crop's require_held_seed docstring.\n"
        "            crop = choose_crop(\n"
        "                farm,\n"
        "                state[\"market_state\"],\n"
        "                private,\n"
        "                day,\n"
        "                unlocked_shops=state.get(\"unlocked_shops\", ()),\n"
        "                start_step=state.get(\"step\"),\n"
        "                opponent_pipeline=state.get(\"opponent_pipeline\"),\n"
        "                require_held_seed=True,\n"
        "            )\n"
        "        if crop and plant_budget.get(crop, 0) > 0:\n"
        "            plant_budget[crop] -= 1\n"
        "            return act_here([\"PLANT\", crop])\n"
    )
    new_block = (
        "    if tile is None:\n"
        "        build_fn = animal_picker or choose_animal_to_build\n"
        "        animal_to_build = build_fn(\n"
        "            farm, private, board_size, day, pending_builds[0], ux, uy\n"
        "        )\n"
        "        if animal_to_build:\n"
        "            pending_builds[0] += 1\n"
        "            structure = ANIMALS[animal_to_build][\"structure\"]\n"
        "            return act_here([f\"BUILD_{structure}\"])\n"
        "        crop_fn = crop_picker or choose_crop\n"
        "        crop = crop_fn(\n"
        "            farm,\n"
        "            state[\"market_state\"],\n"
        "            private,\n"
        "            day,\n"
        "            unlocked_shops=state.get(\"unlocked_shops\", ()),\n"
        "            start_step=state.get(\"step\"),\n"
        "            opponent_pipeline=state.get(\"opponent_pipeline\"),\n"
        "        )\n"
        "        if crop and plant_budget.get(crop, 0) <= 0:\n"
        "            # Top pick can't be planted this turn (zero held seed, chosen\n"
        "            # via can_afford) - fall back to the best-scoring crop we\n"
        "            # actually hold seed for, rather than wasting the turn. See\n"
        "            # choose_crop's require_held_seed docstring.\n"
        "            crop = crop_fn(\n"
        "                farm,\n"
        "                state[\"market_state\"],\n"
        "                private,\n"
        "                day,\n"
        "                unlocked_shops=state.get(\"unlocked_shops\", ()),\n"
        "                start_step=state.get(\"step\"),\n"
        "                opponent_pipeline=state.get(\"opponent_pipeline\"),\n"
        "                require_held_seed=True,\n"
        "            )\n"
        "        if crop and plant_budget.get(crop, 0) > 0:\n"
        "            plant_budget[crop] -= 1\n"
        "            return act_here([\"PLANT\", crop])\n"
    )
    assert src.count(old_block) == 1, "priority-9 plant block not found"
    src = src.replace(old_block, new_block, 1)

    # RECON-ONLY ADDITION between priorities 6 and 7: walk to the shed to
    # fetch a bought animal still waiting for its home. base_backbone's own
    # ladder only picks one up OPPORTUNISTICALLY (priority 5's shed errand,
    # only fires if a unit already happens to be shed-adjacent) - fine at
    # base_backbone's own small MAX_ANIMALS, where luck alone gets a unit
    # there often enough. A reconstructed herd this large needs a unit
    # actively sent to fetch it, or purchases pile up unplaced in the shed
    # indefinitely once the first built structure sits unfilled - measured
    # directly: without this, macro_choose_animal_to_build (mirroring
    # base_backbone's own choose_animal_to_build) never builds a second
    # structure while the first is still unfilled, so the herd stalls at
    # 1-2 real placed animals no matter how many get bought.
    old_p67_boundary = (
        "    urgent_target = _closer_target(ux, uy, harvest_target, water_target)\n"
        "    if urgent_target:\n"
        "        moved = walk_to(urgent_target)\n"
        "        if moved:\n"
        "            return moved\n"
        "\n"
        "    # 7. Carrying an animal we haven't placed yet - go find it a home.\n"
    )
    new_p67_boundary = (
        "    urgent_target = _closer_target(ux, uy, harvest_target, water_target)\n"
        "    if urgent_target:\n"
        "        moved = walk_to(urgent_target)\n"
        "        if moved:\n"
        "            return moved\n"
        "\n"
        "    # 6b. RECON-ONLY: fetch a bought-but-uncollected animal from the\n"
        "    # shed, if one is waiting and we're not carrying anything else.\n"
        "    if animal_in_hand is None and not is_shed_adjacent(ux, uy, board_size):\n"
        "        _, unfilled_for_fetch = scan_animal_structures(farm, board_size)\n"
        "        if unfilled_for_fetch > 0 and any(\n"
        "            private.get(\"shed\", {}).get(a, 0) > 0 for a in ACTIVE_ANIMALS\n"
        "        ):\n"
        "            moved = walk_to(nearest_shed_tile(ux, uy, board_size))\n"
        "            if moved:\n"
        "                return moved\n"
        "\n"
        "    # 7. Carrying an animal we haven't placed yet - go find it a home.\n"
    )
    assert src.count(old_p67_boundary) == 1, "priority 6/7 boundary not found"
    src = src.replace(old_p67_boundary, new_p67_boundary, 1)

    # RECON-ONLY FIX to priority 5's own pickup loop: it grabs the first
    # ACTIVE_ANIMALS species with ANY shed stock, with no check that a
    # matching structure is actually the one sitting unfilled - fine when
    # there is usually at most one species/structure kind in flight at
    # once, wrong for a multi-species herd where a COW can sit in the shed
    # while the only empty structure is a COOP (needs GOOSE): the unit
    # picks up the wrong species, can never place it (priority 4/7 require
    # a matching structure kind), and camps that carry state for the rest
    # of the game - measured directly: placed counts stalled for 9+ days
    # once this happened. Only pick up a species whose OWN structure kind
    # is actually among the unfilled ones.
    old_p5_pickup = (
        "        if animal_in_hand is None:\n"
        "            _, unfilled = scan_animal_structures(farm, board_size)\n"
        "            if unfilled > 0:\n"
        "                for animal in ACTIVE_ANIMALS:\n"
        "                    if shed.get(animal, 0) > 0:\n"
        "                        return act_here([\"PICKUP\", animal, 1])\n"
    )
    new_p5_pickup = (
        "        if animal_in_hand is None:\n"
        "            _, unfilled = scan_animal_structures(farm, board_size)\n"
        "            if unfilled > 0:\n"
        "                unfilled_kinds = {\n"
        "                    t.get(\"kind\") for row in (farm.get(\"tiles\") or []) for t in row\n"
        "                    if isinstance(t, dict) and t.get(\"kind\") in ANIMAL_STRUCTURE_KINDS\n"
        "                    and \"animal\" not in t\n"
        "                }\n"
        "                for animal in ACTIVE_ANIMALS:\n"
        "                    if (\n"
        "                        shed.get(animal, 0) > 0\n"
        "                        and ANIMALS.get(animal, {}).get(\"structure\") in unfilled_kinds\n"
        "                    ):\n"
        "                        return act_here([\"PICKUP\", animal, 1])\n"
    )
    assert src.count(old_p5_pickup) == 1, "priority-5 pickup loop not found"
    src = src.replace(old_p5_pickup, new_p5_pickup, 1)

    # Same species/structure-kind match for the new 6b fetch-from-shed
    # priority added above.
    old_p6b_cond = (
        "    if animal_in_hand is None and not is_shed_adjacent(ux, uy, board_size):\n"
        "        _, unfilled_for_fetch = scan_animal_structures(farm, board_size)\n"
        "        if unfilled_for_fetch > 0 and any(\n"
        "            private.get(\"shed\", {}).get(a, 0) > 0 for a in ACTIVE_ANIMALS\n"
        "        ):\n"
        "            moved = walk_to(nearest_shed_tile(ux, uy, board_size))\n"
        "            if moved:\n"
        "                return moved\n"
    )
    new_p6b_cond = (
        "    if animal_in_hand is None and not is_shed_adjacent(ux, uy, board_size):\n"
        "        _, unfilled_for_fetch = scan_animal_structures(farm, board_size)\n"
        "        if unfilled_for_fetch > 0:\n"
        "            unfilled_kinds_for_fetch = {\n"
        "                t.get(\"kind\") for row in (farm.get(\"tiles\") or []) for t in row\n"
        "                if isinstance(t, dict) and t.get(\"kind\") in ANIMAL_STRUCTURE_KINDS\n"
        "                and \"animal\" not in t\n"
        "            }\n"
        "            shed_for_fetch = private.get(\"shed\", {})\n"
        "            if any(\n"
        "                shed_for_fetch.get(a, 0) > 0\n"
        "                and ANIMALS.get(a, {}).get(\"structure\") in unfilled_kinds_for_fetch\n"
        "                for a in ACTIVE_ANIMALS\n"
        "            ):\n"
        "                moved = walk_to(nearest_shed_tile(ux, uy, board_size))\n"
        "                if moved:\n"
        "                    return moved\n"
    )
    assert src.count(old_p6b_cond) == 1, "priority-6b fetch condition not found"
    src = src.replace(old_p6b_cond, new_p6b_cond, 1)

    old_dma_sig = (
        "def decide_market_actions(\n"
        "    farm, private, market_state, day, reserved_wheat=0, unlocked_shops=(), start_step=None,\n"
        "    opponent_pipeline=None,\n"
        "):"
    )
    new_dma_sig = (
        "def decide_market_actions(\n"
        "    farm, private, market_state, day, reserved_wheat=0, unlocked_shops=(), start_step=None,\n"
        "    opponent_pipeline=None, crop_picker=None,\n"
        "):"
    )
    assert src.count(old_dma_sig) == 1, "decide_market_actions signature not found"
    src = src.replace(old_dma_sig, new_dma_sig, 1)

    old_dma_call = (
        "    # Buy exactly one seed of our preferred next crop, if it makes sense.\n"
        "    preferred_crop = choose_crop(\n"
        "        farm, market_state, private, day, unlocked_shops=unlocked_shops,\n"
        "        start_step=start_step, opponent_pipeline=opponent_pipeline,\n"
        "    )"
    )
    new_dma_call = (
        "    # Buy exactly one seed of our preferred next crop, if it makes sense.\n"
        "    preferred_crop = (crop_picker or choose_crop)(\n"
        "        farm, market_state, private, day, unlocked_shops=unlocked_shops,\n"
        "        start_step=start_step, opponent_pipeline=opponent_pipeline,\n"
        "    )"
    )
    assert src.count(old_dma_call) == 1, "decide_market_actions preferred_crop call not found"
    src = src.replace(old_dma_call, new_dma_call, 1)

    # Rename the base entrypoint so this file can define its own `agent`.
    src = src.replace(
        "def base_backbone_agent(obs):",
        "def _agent_base_backbone(obs):",
        1,
    )
    # Drop base_backbone's own trailing `agent = base_backbone_agent` line -
    # this file supplies its own, later, as the true last callable.
    src = src.replace(
        "\n# The framework picks the LAST callable in this module's namespace - not a\n"
        "# function named `agent` (kaggle_environments/agent.py:64). Anything callable\n"
        "# defined below this line silently becomes the submission instead, the episode\n"
        "# still reports DONE, every action is discarded as invalid, and the agent\n"
        "# finishes on exactly its starting money. Keep this binding last.\n"
        "agent = base_backbone_agent\n",
        "",
        1,
    )
    return src


def embed_routes_blob(routes, var_name):
    raw = json.dumps(routes).encode("utf-8")
    blob = base64.b85encode(zlib.compress(raw, 9)).decode("ascii")
    return (
        f"{var_name}_DATA = '{blob}'\n"
        f"{var_name} = __import__('json').loads("
        f"__import__('zlib').decompress(__import__('base64').b85decode({var_name}_DATA)))\n"
    )


if __name__ == "__main__":
    routes_path, out_path, module_tag = sys.argv[1], sys.argv[2], sys.argv[3]
    with open(routes_path) as f:
        routes = json.load(f)
    patched = load_base_backbone_patched()
    blob_src = embed_routes_blob(routes, f"_{module_tag}_ROUTES")
    with open(out_path, "w") as f:
        f.write(patched)
        f.write("\n\n# " + "=" * 71 + "\n")
        f.write(f"# Embedded macro routes for {module_tag}, one per turn-72 opening shop key.\n")
        f.write("# " + "=" * 71 + "\n\n")
        f.write(blob_src)
    print(f"wrote base+blob to {out_path}, {len(routes)} route keys, blob {len(blob_src)} chars")
