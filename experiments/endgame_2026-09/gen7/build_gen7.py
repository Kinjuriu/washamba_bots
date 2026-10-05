"""Build a route-generation-7 agent: v15stack's chassis (Apache-2.0, unchanged) replaying routes
extracted from one top-6 team's recent ladder games, routed by the first two shop unlocks at step 144.
Usage: python build_gen7.py routes.json.gz out.py [switch_steps]"""
import gzip, json, sys, collections, base64, zlib
routes_file, out = sys.argv[1], sys.argv[2]
switch = [int(x) for x in (sys.argv[3] if len(sys.argv) > 3 else '144').split(',')]
src = open('/home/claude/kag/agents/v15stack/main.py').read().split('\n')
cut = next(i for i, l in enumerate(src) if l.startswith('import base64'))
chassis = '\n'.join(src[:cut])
R = json.load(gzip.open(routes_file))
# default route: winner whose turn-72 prefix is the most common; tie-break by margin
pref = collections.Counter(json.dumps(r['actions'][:72]) for r in R if r['won'])
top_pref = pref.most_common(1)[0][0]
cands = [r for r in R if r['won'] and json.dumps(r['actions'][:72]) == top_pref]
default = max(cands, key=lambda r: r['margin'])
routes = [default] + [r for r in R if r is not default]
key2, key1 = {}, {}
for i, r in enumerate(routes):
    if not r['won']: continue
    k2 = tuple(r['shops'][:2]); k1 = tuple(r['shops'][:1])
    if k2 not in key2 or r['margin'] > routes[key2[k2]]['margin']: key2[k2] = i
    if k1 not in key1 or r['margin'] > routes[key1[k1]]['margin']: key1[k1] = i
data = dict(actions=[r['actions'] for r in routes], key2=[[list(k), v] for k, v in key2.items()], key1=[[list(k), v] for k, v in key1.items()])
blob = base64.b85encode(zlib.compress(json.dumps(data, separators=(',', ':')).encode(), 9)).decode()
tail = f'''

# ---------------------------------------------------------------------------
# Washamba Bots route generation 7 ({routes_file.split('/')[-1]}), built {__import__('datetime').date.today()}.
# Chassis above: v15stack (wzhengbiao) and upstream authors, Apache-2.0, unchanged.
# Routes: {len(routes)} recorded public ladder trajectories; router keyed by the first two shop unlocks.
import base64 as _g7b, json as _g7j, zlib as _g7z
_G7 = _g7j.loads(_g7z.decompress(_g7b.b85decode({blob!r})))
_G7_ROUTES = {{i: a for i, a in enumerate(_G7['actions'])}}
_G7_KEY2 = {{tuple(k): v for k, v in _G7['key2']}}
_G7_KEY1 = {{tuple(k): v for k, v in _G7['key1']}}
_G7_SWITCH = {switch!r}
del _G7
def _g7_router(observation, step, state):
    if 'route' not in state:
        state['route'] = 0
    for s in _G7_SWITCH:
        if step >= s and state.get('done') != s and (state.get('done') or 0) < s:
            shops = tuple((_get(_get(observation, 'town', {{}}), 'unlocked_shops', []) or [])[:2])
            r = _G7_KEY2.get(shops)
            if r is None:
                r = _G7_KEY1.get(shops[:1], state['route'])
            state['route'] = r
            state['done'] = s
    return state['route']
_G7_IMPL = make_agent(_G7_ROUTES, router=_g7_router, hand_align=True, weed_repair=True, sell_lead=True)
def agent(observation, configuration=None):
    try:
        return _G7_IMPL(observation, configuration)
    except Exception:
        return {{'farmer': ['PASS'], 'hands': [], 'market': []}}
'''
open(out, 'w').write(chassis + tail)
print(out, 'routes', len(routes), 'key2', len(key2), 'key1', len(key1), 'default margin', default['margin'])
