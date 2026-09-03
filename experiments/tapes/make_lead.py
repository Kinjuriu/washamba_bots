"""Write <base> + sell-advance rim with lookahead K to out path."""
import sys, re
base, K, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
src = open(base, encoding="utf-8").read()
RIM = '''
LEAD_K = %d
LEAD_START = 144
LEAD_SKIP = ("WHEAT", "FERTILIZER")
_lead_used = set()

def _advance_sells(observation, action, tape_name, tape, step):
    """Pull the tape's upcoming SELL orders (next LEAD_K steps, same tape) forward
    to now when the shed already holds the goods. Tape orders first, cap 10."""
    global _lead_used
    if step <= 1:
        _lead_used = set()
    market = list(action.get("market") or [])
    for i, o in enumerate(list(market)):
        if (tape_name, step, i) in _lead_used:
            market.remove(o)
    action["market"] = market
    if step < LEAD_START:
        return action
    shed = dict(_get(_get(observation, "private", {}) or {}, "shed", {}) or {})
    for o in market:
        if o and o[0] == "SELL" and len(o) > 2:
            shed[o[1]] = (shed.get(o[1], 0) or 0) - int(o[2])
    for s in range(step + 1, min(step + LEAD_K, len(tape) - 1) + 1):
        fut = (tape[s] or {}).get("market") or []
        for i, o in enumerate(fut):
            if len(market) >= 10:
                return action
            if not o or o[0] != "SELL" or len(o) < 3 or o[1] in LEAD_SKIP:
                continue
            if (tape_name, s, i) in _lead_used:
                continue
            q = int(o[2])
            if (shed.get(o[1], 0) or 0) >= q:
                market.append(list(o)); shed[o[1]] -= q
                _lead_used.add((tape_name, s, i))
    action["market"] = market
    return action
''' % K
src = src.replace("\ndef agent(observation, configuration=None):", RIM + "\ndef agent(observation, configuration=None):", 1)
src = src.replace("        tape = _TAPES[_which(step, shops)]\n", "        tape_name = _which(step, shops); tape = _TAPES[tape_name]\n", 1)
src = src.replace("        action.setdefault(\"farmer\", [\"PASS\"]); action.setdefault(\"market\", [])\n        return action\n",
                  "        action.setdefault(\"farmer\", [\"PASS\"]); action.setdefault(\"market\", [])\n        return _advance_sells(observation, action, tape_name, tape, step)\n", 1)
assert "_advance_sells(observation" in src and "tape_name = _which" in src
open(out, "w", encoding="utf-8").write(src)
print("wrote", out)
