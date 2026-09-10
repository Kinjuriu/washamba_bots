"""Fixture proving exactly when a demand tick's price refresh becomes visible
to an agent, and nailing down the off-by-one that bit us before: a replay's
env.steps[i].observation is what the agent SAW when it chose
env.steps[i].action, but that action's effects (and any tick that fires
during the same interpreter call) only show up in env.steps[i+1].observation.

Engine mechanics behind this (kaggriculture.py's interpreter(), read directly
rather than assumed - "engine is the source of truth", CLAUDE.md):

    step = obs0.step                  # the step the agent's action responds to
    ... apply unit actions ...
    _process_market(state, env)       # OUR sell/buy orders commit here, against
                                       # the price already in market["prices"]
    _town_consume(env, state, step)   # if step % interval == 0: shop/center
                                       # inventory drops, THEN _refresh_prices()
    ... next_step = step + 1 ...      # only now does the refreshed price become
                                       # visible, in the observation at next_step

So a tick that fires "on step S" (S % interval == 0) refreshes the price
agents see starting at observation step S+1, not S. To sell into the
refreshed price, submit the SELL order in response to an observation whose
step satisfies (step - 1) % interval == 0, i.e. step % interval == 1 - never
step % interval == 0.

This is checked two ways:
  1. Empirically, off a real played episode (`pass` vs `pass`, so no agent
     order ever moves the market - the only price movement is town/shop
     demand). Confirms the +1 alignment and the plateau in between.
  2. Directly off the engine's own market_price(), computed from a
     TOWN_CENTER_PRODUCT's known per-tick consumption, so the empirical
     read is checked against the formula rather than just against itself.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kaggle_environments import make
from kaggle_environments.envs.kaggriculture.kaggriculture import (
    MARKET_PARAMS,
    TOWN_CENTER_PRODUCTS,
    market_price,
)

CENTER_INTERVAL = 24
SHOP_INTERVAL = 4
TRACK_ITEM = "WHEAT"  # a TOWN_CENTER_PRODUCT, always consumed regardless of
                       # which shops have unlocked


def _play_and_record(seed=0, steps=60):
    """Run `pass` vs `pass` (neither ever submits a market order) and record
    (obs.step, price, inventory) for TRACK_ITEM at every recorded index.
    """
    env = make("kaggriculture", configuration={"episodeSteps": steps + 2, "seed": seed}, debug=False)
    env.run(["pass", "pass"])
    trace = []
    for row in env.steps:
        obs = row[0].observation
        market = obs["market"]
        trace.append((obs["step"], market["prices"][TRACK_ITEM], market["inventory"][TRACK_ITEM]))
    return trace


class TestDemandTickAlignment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert TRACK_ITEM in TOWN_CENTER_PRODUCTS, "test item must be a town-center product"
        cls.trace = _play_and_record(seed=0, steps=CENTER_INTERVAL * 2 + 2)
        # index by step for convenience; env.steps is one row per recorded
        # step, step 0 first.
        cls.by_step = {step: (price, inv) for step, price, inv in cls.trace}

    def test_no_shops_unlocked_early_no_market_orders(self):
        # Self-check on the fixture's own premise: with `pass` on both sides
        # the only thing that can move TRACK_ITEM's price this early is the
        # town-center tick, so any movement we see is attributable to it.
        self.assertIn(0, self.by_step)
        self.assertIn(CENTER_INTERVAL * 2 + 1, self.by_step)

    def test_tick_at_step_0_is_invisible_at_step_0(self):
        # Step 0 observation is the pristine starting market - the interpreter
        # hasn't run yet when the agent sees it.
        price0, inv0 = self.by_step[0]
        self.assertEqual(inv0, 10000, "step-0 observation must be the untouched starting inventory")

    def test_tick_at_step_0_lands_by_step_1(self):
        # The step-0 interpreter call fires the center tick (0 % 24 == 0) and
        # refreshes prices before advancing to step 1 - so step 1's
        # observation, not step 0's, is the first to show it.
        price0, inv0 = self.by_step[0]
        price1, inv1 = self.by_step[1]
        self.assertLess(inv1, inv0, "inventory must have dropped by observation step 1")
        self.assertGreaterEqual(price1, price0, "price must refresh upward as inventory falls below I0")

    def test_plateau_between_ticks(self):
        # No agent orders and no shop consumption of TRACK_ITEM competing
        # here (SHOP_INTERVAL only matters once a shop selling WHEAT is
        # unlocked, which doesn't happen at step 0) - so price/inventory
        # should be flat from step 1 up to and including step 24, then move
        # again only once the step-24 tick lands at step 25.
        first = self.by_step[1]
        for step in range(1, CENTER_INTERVAL + 1):
            if step not in self.by_step:
                continue
            self.assertEqual(
                self.by_step[step], first,
                f"step {step} should be flat with step 1 (no tick fires in between) "
                f"unless a shop selling {TRACK_ITEM} unlocked and consumed it",
            )

    def test_second_center_tick_lands_one_step_after_step_24(self):
        price24, inv24 = self.by_step[CENTER_INTERVAL]
        price25, inv25 = self.by_step[CENTER_INTERVAL + 1]
        self.assertLess(inv25, inv24, "the step-24 tick's inventory drop must appear at step 25, not step 24")

    def test_formula_matches_empirical_price_after_two_center_ticks(self):
        # After exactly two center ticks (steps 0 and 24) with no shop
        # consumption and no agent orders, inventory should be exactly
        # 10000 - 2, and market_price() on that inventory should equal what
        # the fixture actually observed at step 25.
        _, inv25 = self.by_step[CENTER_INTERVAL + 1]
        self.assertEqual(inv25, 10000 - 2)
        price25, _ = self.by_step[CENTER_INTERVAL + 1]
        # market_price(item, inventory, params) expects `params` to be a
        # whole item-keyed table like MARKET_PARAMS (it does params[item]
        # internally), not a single item's params sub-dict - pass the table.
        expected = market_price(TRACK_ITEM, inv25, MARKET_PARAMS)
        self.assertEqual(price25, expected)

    def test_sell_window_rule_is_step_mod_interval_equals_1(self):
        # This is the rule Agent A's selling logic is built on: an
        # observation's step is "freshly past a center tick" iff
        # (step - 1) % CENTER_INTERVAL == 0, equivalently step % CENTER_INTERVAL == 1 -
        # never step % CENTER_INTERVAL == 0, which is the pre-tick step.
        for step, (price, inv) in self.by_step.items():
            in_window = step % CENTER_INTERVAL == 1
            just_dropped = step - 1 in self.by_step and inv < self.by_step[step - 1][1]
            if just_dropped:
                self.assertTrue(
                    in_window,
                    f"inventory dropped arriving at step {step}, so step % {CENTER_INTERVAL} must be 1, "
                    f"got {step % CENTER_INTERVAL}",
                )


if __name__ == "__main__":
    unittest.main()
