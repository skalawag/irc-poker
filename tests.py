#! /usr/bin/env python

import unittest
import irc_poker as ircp

class TestDealer(unittest.TestCase):
    def setUp(self):
        self.players = ['fyv', 'wag', 'fwwl', 'barney', 'fred']
        self.d = ircp.Dealer('fyv', 'wag', 'fwwl', 'barney', 'fred')
        self.d.new_hand()

    def tearDown(self):
        del(self.d)

    def test__init__(self):
        names = sorted(['fyv', 'wag', 'fwwl', 'barney', 'fred'])
        tar = sorted([h.player.name for h in self.d.active])
        self.assertEqual(names,tar)

    def test_active_contents(self):
        self.assertEqual(type(self.d), type(self.d.active[0]))

    def test_is_stage_over_betandcall(self):
        self.d.get_hand_by_name('fwwl').act = 'bet'
        for hand in self.d.active:
            if hand.player.name != 'fwwl':
                hand.act = 'call'
        self.assertTrue(self.d.is_stage_over())

    def test_is_stage_over_all_allin(self):
        for hand in self.d.active:
            hand.act = 'bet'
            hand.all_in = True
        self.assertTrue(self.d.is_stage_over())

    def test_is_stage_over_all_checks(self):
        for hand in self.d.active:
            hand.act = 'check'
        self.assertTrue(self.d.is_stage_over())

    def test_is_stage_over_raise_plus_calls(self):
        for hand in self.d.active:
            hand.act = 'call'
        self.d.active[-1].act = 'raise'
        self.assertTrue(self.d.is_stage_over())

    def test_is_stage_over_1_player(self):
        self.d.active = self.d.active[:1]
        self.assertTrue(self.d.is_stage_over())

    def test_clear_line_bets_even(self):
        for hand in self.d.active:
            hand.bet = 40
        self.d.clear_line_bets()
        def cmpr(x,y):
            if x < y: return 1
            elif x == y: return 0
            else: return -1
        def key(x):
            return x.player.name
        source = sorted(self.d.active, cmp=cmpr, key=key)
        tar = sorted(self.d.pots[1]['contenders'], cmp=cmpr, key=key)
        self.assertEqual(source,tar)

    def test_clear_line_bets_uneven(self):
        for hand in self.d.active:
            hand.bet = 40
        for hand in self.d.active[2:]:
            hand.bet = 80
        self.d.clear_line_bets()
        self.assertEqual(len(self.d.pots), 2)

    def test_clear_line_bets_odd_man(self):
        for hand in self.d.active:
            hand.bet = 40
        for hand in self.d.active[2:]:
            hand.bet = 80
        self.d.active[-1].bet = 100
        self.d.clear_line_bets()
        self.assertEqual(len(self.d.pots), 2)

    def test_assign_winners_to_pots_simple_pot(self):
        self.d.pots = {1: {'contenders': self.d.active, 'amt': 500, 'winners': []}}
        for hand in self.d.active:
            print hand, hand.player.chips
        self.d.eval_hands()
        self.d.assign_winners_to_pots()
        self.d.payout()
        print self.d.pots
        for hand in self.d.active:
            print hand, hand.player.chips

if __name__ == '__main__':
    unittest.main()
