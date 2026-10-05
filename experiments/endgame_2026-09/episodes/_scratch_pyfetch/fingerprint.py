import gzip, json

DSM_PREFIX = [["BUY_ANIMAL", "COW", 1], ["BUY_PRODUCT", "WHEAT", 5]]
BOEY_FIRST = ["BUY_PRODUCT", "WHEAT", 3]
TAPE_NEEDLES = [["BUY_ANIMAL", "COW", 2], ["BUY_ANIMAL", "SHEEP", 2]]

def load_replay(path):
    return json.load(gzip.open(path))

def seat_action(replay, row, seat):
    st = replay['steps']
    if row >= len(st):
        return None
    return st[row][seat]['action']

def classify(replay, seat):
    a1 = seat_action(replay, 1, seat)
    a2 = seat_action(replay, 2, seat)
    m1 = a1['market'] if a1 else []
    m2 = a2['market'] if a2 else []

    # DSM family: row-1 market orders' first two entries equal the DSM opening prefix
    if len(m1) >= 2 and m1[0] == DSM_PREFIX[0] and m1[1] == DSM_PREFIX[1]:
        return 'DSM', m1, m2

    # Boey: row-1 starts with BUY_PRODUCT WHEAT 3 followed by five HIREs
    if len(m1) >= 6 and m1[0] == BOEY_FIRST and all(o == ['HIRE'] for o in m1[1:6]):
        return 'Boey', m1, m2

    # tape family: row-2 market orders contain both COW,2 and SHEEP,2 buy-animal orders
    if all(any(o == needle for o in m2) for needle in TAPE_NEEDLES):
        return 'tape', m1, m2

    return 'other', m1, m2
