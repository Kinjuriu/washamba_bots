"""WB_SellEngine: when and how much to sell (FABLE_IDEAS section 1, section 5 items 3/4/7).

Owner: Builder A (splice build, docs/ENDGAME/splice_build.md). Stateless: every call
reads only the observation and the controller's `sellable` release, so a skipped call or
a dropped order costs nothing but the sale. CALL IT EVERY TURN (glut sales and the shed
valve fire off-cadence).

Default configuration = FABLE section 1, with one measured correction:
- CADENCE: healthy markets are sold on obs["step"] % 4 == 1 only (`healthy_phases`).
  Shops consume at the end of the interpreter call for steps s % 4 == 0 (after that
  call's market), so s + 1 is the first call quoted on the drained inventory (proved on
  the engine by experiments/splice/_probe_cadence.py; in env.steps terms the action at
  row % 4 == 2).
- SLICES: per selling turn, the units the last shop tick consumed + headroom_share of the
  units below I0, at least 1, and at least enough to clear the release within
  hold_windows selling turns (or before the season ends). EGG, WHEAT and FERTILIZER are
  near-flat above I0 and are sold whole. Scarcity-taking: a quote >= 1.4 x base sells
  down to 1.3 x base, never below.
- CORRECTION, replacing FABLE's decaying quote threshold: a GLUT (no unlocked shop
  consumes the item, or its market sits above I0 by more than glut_days = 0.5 of its
  daily drain) sells the whole release on any turn. The drain cannot recover the price
  before the next sale, so a held unit is later sold into a deeper glut. Against W3 the
  threshold held 29 milk into a crash and sold it at 1-5 while the tape sold at 32-79.

Mirror-tuned alternative (docs/ENDGAME/splice_sell_engine.md section 4): set
healthy_phases = (0, 1, 2, 3) and contested_dumps = True. Contested = the other farm has
a producer of the item (sheep: wool, cows: milk, geese: eggs, any animal: fertilizer, a
planted crop); such releases are then sold whole on arrival. It reached price parity with
W3 in mirrors, where the spec config realized ~2 less per unit, but both effects come
from W3 dropping the same goods on the same turn, which a non-tape controller will not
reproduce. The coordinator decides; the default stays spec-faithful.

Endgame: the final processed turn (obs step 718) sells everything; before it the
clearance term spreads what is left over the remaining selling turns. Shed valve (any
turn): if shed plus carried goods would pass the 100-item cap, sell the release down to
a safe level, least-harm units first (overflow is discarded silently).

Output: at most `slots` orders; if truncation is needed the highest-revenue orders
survive, then they are placed by per-unit quote, dearest in slot 0, because slot i of
both players runs to completion before slot i+1 (engine _process_market).

Build notes: concatenated after the base agent and price_model.py, so every top-level
name carries WB_ / _wb_; the import line below is dropped by experiments/splice/build.py.
"""
from price_model import WB_PriceModel  # noqa: F401  (dropped by build.py)

WB_SE_PREMIUM = ("WOOL", "MILK", "STRAWBERRY")
WB_SE_UNPACED = ("EGG", "WHEAT", "FERTILIZER")   # log / shallow-linear above I0
WB_SE_FINAL_STEP = 718         # last obs step whose action is processed when episodeSteps = 720
WB_SE_PRODUCER = {"WOOL": "SHEEP", "MILK": "COW", "EGG": "GOOSE"}   # animal products; crops by name


def _wb_ceil_div(a, b):
    return -(-a // b)


def _wb_ceil(x):
    """Ceiling of a non-negative float, as an int."""
    i = int(x)
    return i + 1 if x > i else i


class WB_SellEngine:
    # Tunables. Class attributes (immutable values) so a sweep can override per instance.
    glut_days = 0.5            # glut: level above I0 > glut_days x daily drain
    healthy_phases = (1,)      # obs["step"] % 4 phases on which a healthy market is sold
    contested_dumps = False    # True: a product the rival also makes is sold whole on arrival
    headroom_share = 0.2       # per selling turn: share of the units below I0 to sell into
    hold_windows = 6           # clear a healthy release within this many selling turns
    min_slice = 1
    scarcity_start = 1.4       # scarcity-taking fires when quote >= 1.4 x base...
    scarcity_stop = 1.3        # ...and sells while the pre-sell quote stays >= 1.3 x base
    shed_valve_high = 90       # shed + carried above this: sell down to shed_valve_low
    shed_valve_low = 80

    def __init__(self, price_model, final_step=WB_SE_FINAL_STEP):
        self.pm = price_model
        self.final_step = int(final_step)

    # ---- schedule and regime -----------------------------------------------------
    def selling_turns_left(self, step):
        """Healthy-market sale opportunities left: turns in [step, final_step) whose
        phase is in healthy_phases, plus the final turn."""
        if step >= self.final_step:
            return 1
        n = 0
        for phase in set(self.healthy_phases):
            first = step + (phase - step) % 4
            if first < self.final_step:
                n += (self.final_step - 1 - first) // 4 + 1
        return n + 1

    def is_glut(self, item, inv, shops):
        """True when holding cannot pay: no shop consumes the item, or its market sits
        more than glut_days of drain above I0."""
        pm = self.pm
        if not self._has_shop_drain(item, shops):
            return True
        return inv - pm.i0(item) > self.glut_days * pm.drain_per_day(item, shops)

    def rival_producers(self, obs):
        """Products the other farm can put on the market: its animals' products (and
        FERTILIZER if it has any animal) and its planted crops. Both farms are public."""
        out = set()
        me = obs.get("player", 0)
        for seat, farm in enumerate(obs.get("farms") or []):
            if seat == me:
                continue
            for row in farm.get("tiles") or []:
                for t in row:
                    if not isinstance(t, dict):
                        continue
                    if "animal" in t:
                        out.add("FERTILIZER")
                        for product, animal in WB_SE_PRODUCER.items():
                            if t["animal"] == animal:
                                out.add(product)
                    elif t.get("kind") == "PLANT":
                        out.add(t.get("crop"))
        return out

    # ---- main entry ---------------------------------------------------------------
    def orders(self, obs, sellable, slots):
        """At most `slots` SELL orders for this turn, most valuable first, slot 0 first.
        `sellable`: units the controller releases for sale this turn (it has already
        removed feed wheat, fertilizer it will apply, etc.). Never sells more than that."""
        if slots is None or slots <= 0 or not sellable:
            return []
        pm = self.pm
        step = int(obs["step"])
        market_inv = obs["market"]["inventory"]
        shops = list(obs["town"]["unlocked_shops"] or [])
        avail = {}
        for item, n in sellable.items():
            if item in pm.params and item in market_inv:
                n = int(n)
                if n > 0:
                    avail[item] = n
        if not avail:
            return []

        plan = {}
        if step >= self.final_step:
            plan = dict(avail)                       # last processed turn: sell everything
        else:
            healthy_turn = step % 4 in self.healthy_phases
            rivals = self.rival_producers(obs) if self.contested_dumps else ()
            turns_left = None
            for item, n in avail.items():
                inv = market_inv[item]
                if self.is_glut(item, inv, shops) or item in rivals:
                    q = n
                elif healthy_turn:
                    if turns_left is None:
                        turns_left = self.selling_turns_left(step)
                    q = self._healthy_qty(item, n, inv, shops, step, turns_left)
                else:
                    q = 0
                if q > 0:
                    plan[item] = q
        self._shed_valve(obs, avail, plan, market_inv)

        rows = []
        for item, q in plan.items():
            inv = market_inv[item]
            rows.append((pm.sell_revenue(item, inv, q), pm.quote(item, inv), item, q))
        if len(rows) > slots:
            rows.sort(key=lambda r: (-r[0], r[2]))
            rows = rows[:slots]
        rows.sort(key=lambda r: (-r[1], -r[0], r[2]))
        return [["SELL", item, q] for (_rev, _quote, item, q) in rows]

    # ---- per-product decision -----------------------------------------------------
    def _healthy_qty(self, item, n, inv, shops, step, turns_left):
        pm = self.pm
        base = pm.base(item)
        if item in WB_SE_UNPACED:
            q = n
        else:
            headroom = max(0, pm.i0(item) - inv)
            budget = pm.tick_drain(item, shops, step) + _wb_ceil(self.headroom_share * headroom)
            clear = _wb_ceil_div(n, max(1, min(turns_left, self.hold_windows)))
            q = min(n, max(budget, self.min_slice, clear))
        if pm.quote(item, inv) >= self.scarcity_start * base:
            q = max(q, pm.units_at_or_above(item, inv, self.scarcity_stop * base, n))
        return q

    def _has_shop_drain(self, item, shops):
        for name in shops:
            products = self.pm.shops.get(name)
            if products and item in products:
                return True
        return False

    def _shed_valve(self, obs, avail, plan, market_inv):
        """Sell extra units when shed + carried goods would overflow the cap tonight."""
        private = obs["private"]
        pressure = sum(int(v) for v in private["shed"].values())
        for inv in private.get("inventories") or []:
            pressure += sum(int(v) for v in inv.values())
        pressure -= sum(plan.values())
        if pressure <= self.shed_valve_high:
            return
        need = pressure - self.shed_valve_low
        pm = self.pm
        cur, key = {}, {}
        for item in avail:
            if plan.get(item, 0) < avail[item]:
                cur[item] = pm.inventory_after_sells(item, market_inv[item], plan.get(item, 0))
                key[item] = pm.quote(item, cur[item]) / pm.base(item)
        while need > 0 and key:
            best = max(key, key=key.get)             # least-harm unit: dearest relative to base
            plan[best] = plan.get(best, 0) + 1
            need -= 1
            if plan[best] >= avail[best]:
                del key[best]
                continue
            if pm.quote(best, cur[best]) > 1:        # $1 sales add no inventory
                cur[best] += 1
                key[best] = pm.quote(best, cur[best]) / pm.base(best)
