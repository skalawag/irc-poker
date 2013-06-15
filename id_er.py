rank_order = ['0x41','0x4b','0x51','0x4a','0x54',
              '0x39','0x38','0x37','0x36','0x35',
              '0x34','0x33','0x32']

straights = [['0x41','0x32','0x33','0x34','0x35'], # A - 5
             ['0x32','0x33','0x34','0x35','0x36'], # 2 - 6
             ['0x33','0x34','0x35','0x36','0x37'], # 3 - 7
             ['0x34','0x35','0x36','0x37','0x38'], # 4 - 8
             ['0x35','0x36','0x37','0x38','0x39'], # 5 - 9
             ['0x36','0x37','0x38','0x39','0x54'], # 6 - T
             ['0x37','0x38','0x39','0x54','0x4a'], # 7 - J
             ['0x38','0x39','0x54','0x4a','0x51'], # 8 - Q
             ['0x39','0x54','0x4a','0x51','0x4b'], # 9 - K
             ['0x54','0x4a','0x51','0x4b','0x41']] # T - A

def __get_rank_of(acard):
    return rank_order.index(acard[0])

# HIGH CARD
def get_hc(alist):
    hc = None
    rank = 20
    for card in alist:
        ind = __get_rank_of(card)
        if ind < rank:
            rank = ind
            hc = card
        if rank == 0:
            break
    return hc

def __sort_by_rank(alist):
    ''' puts cards by rank together '''

    sorts = {}
    for card in alist:
        rank = __get_rank_of(card)
        try:
            sorts[rank].append(card)
        except:
            sorts.setdefault(rank,[card])
    return sorts

def __filter_nips(adict,n):
    tar = []
    for key in adict.keys():
        if len(adict[key]) == n:
            for item in adict[key]:
                tar.append(item)
    tar.sort()
    return tar

# PAIRS (ALL)
def get_pairs(alist):
    ''' return all pairs in alist '''

    # sort cards by rank
    sorts = __sort_by_rank(alist)
    # get target
    pairs = __filter_nips(sorts,2)
    if pairs != []: return pairs
    else: return None

# BEST PAIR
def get_best_pair(alist):
    pairs = get_pairs(alist)
    if pairs != [] and pairs != None:
        pairs = __sort_by_rank(pairs)
        keys = sorted(pairs.keys())
        return pairs[keys[0]]

# TWO PAIR
def get_two_pair(alist):
    pairs = get_pairs(alist)
    if pairs == None:
        return
    else:
        pairs = __sort_by_rank(pairs)
    keys = pairs.keys()[:2]
    tar = []
    if len(keys) > 1:
        tar = pairs[keys[0]] + pairs[keys[1]]
        tar.sort()
    if tar != []: return tar
    else: return None

# TRIPS
def get_trips(alist):
    # sort cards by rank
    sorts = __sort_by_rank(alist)
    # get target
    trips = __filter_nips(sorts,3)
    if trips != []: return trips
    else: return None

# FULL HOUSE
def get_full_house(alist):
    reserve = get_trips(alist)
    if reserve == None:
        return
    try:
        tar = __sort_by_rank(reserve[:])
        trip = tar[sorted(tar.keys())[0]]
    except: trip = []
    try:
        tar = __sort_by_rank(get_pairs(alist))
        pair = tar[sorted(tar.keys())[0]]
    except: pair = []
    if len(trip) != 0 and len(pair) != 0:
        fh = trip + pair
        fh.sort()
        return fh
    if len(reserve) == 6:
        sorts = __sort_by_rank(reserve)
        keys = sorts.keys()[:2]
        sorts[keys[1]].pop()
        fh = sorts[keys[0]] + sorts[keys[1]]
        fh.sort()
        return fh

# QUADS
def get_quads(alist):
    # sort cards by rank
    sorts = __sort_by_rank(alist)
    # get target
    quads = __filter_nips(sorts,4)
    if quads != []: return quads
    else: return None

# STRAIGHT
def get_straight(alist):
    straight_cards = []
    counted = []
    for straight in straights:
        counter = 0
        for card in alist:
            if card[0] in straight and card[0] not in counted:
                counted.append(card[0])
                counter += 1
                straight_cards.append(card)
        if counter == 5:
            straight_cards.sort()
            return straight_cards
        else:
            counted = []
            straight_cards = []

def __sort_by_suit(alist):
    c = []; d = []; h = []; s = []
    for card in alist:
        if card[1] == '0x63':
            c.append(card)
        elif card[1] == '0x64':
            d.append(card)
        elif card[1] == '0x68':
            h.append(card)
        elif card[1] == '0x73':
            s.append(card)
    return c,d,h,s

def __move_some(suit):
    ''' extract best five suited '''
    bin = []
    while 1:
        hi = get_hc(suit)
        if hi != None:
            bin.append(hi)
            suit.remove(hi)
        if len(bin) == 5:
            break
    bin.sort()
    return bin

# FLUSH
def get_flush(alist):
    sorts = __sort_by_suit(alist)
    if len(sorts[0]) == 5:
        sorts[0].sort()
        return sorts[0]
    elif len(sorts[0]) > 5:
        return __move_some(sorts[0])
    if len(sorts[1]) == 5:
        sorts[1].sort()
        return sorts[1]
    elif len(sorts[1]) > 5:
        return __move_some(sorts[1])
    if len(sorts[2]) == 5:
        sorts[2].sort()
        return sorts[2]
    elif len(sorts[2]) > 5:
        return __move_some(sorts[2])
    if len(sorts[3]) == 5:
        sorts[3].sort()
        return sorts[3]
    elif len(sorts[3]) > 5:
        return __move_some(sorts[3])

# STRAIGHT FLUSH
def get_straight_flush(alist):
    st = get_straight(alist)
    fl = get_flush(alist)
    if not st or not fl:
        return
    if sorted(st) == sorted(fl):
        return st

def id_cards(alist):
    sf = get_straight_flush(alist)
    if sf: return sf,'STRFL'
    fk = get_quads(alist)
    if fk: return fk,'4K'
    fh = get_full_house(alist)
    if fh: return fh,'FH'
    fl = get_flush(alist)
    if fl: return fl,'FL'
    st = get_straight(alist)
    if st: return st,'STR'
    tr = get_trips(alist)
    if tr: return tr,'3K'
    tp = get_two_pair(alist)
    if tp: return tp,'2P'
    p = get_best_pair(alist)
    if p: return p,'P'
    return get_hc(alist),'HC'

def main(alist):
    reserve = alist[:]
    idd = id_cards(alist)
    made = idd[0]
    name = idd[1]
    rest = [x for x in reserve if x not in made]
    return made, rest, name

if __name__ == '__main__':
    from dealer import convert
    cards = [('A', 's'), ('A', 'h'), ('J', 's'), ('2', 'c'), ('5', 'd')]
    #[('A', 'c'), ('2','s'), ('3','c'), ('4','h'), ('5','d')]
    cards = [convert(c) for c in cards]
    res = main(cards)
    print res
