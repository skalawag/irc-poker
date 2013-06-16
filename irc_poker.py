#! /usr/bin/env python
# coding=utf-8
"""
irc-poker.py - Phenny Texas Holdem Module
Copyright 2012, Mark Scala
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""
import random
import ranker
import time

class Player:
    def __init__(self,name,chips=None):
        self.name = name
        if chips:
            self.chips = chips
        else:
            self.chips = 0

class Dealer:
    def __init__(self, *args):
        self.players = [Player(x,chips=1000) for x in args]
        self.sitting_out = []
        self.folded = []
        # needed if a player joins in the middle of a hand.
        self.on_deck = []
        self.active = []
        self.deck = None
        self.stage = None
        self.pots = {}
        self.game_on = False
        self.th_start = False
        self.bet_to_call = 0
        self.bb = 20
        self.sb = 10
        self.dead_raise = False
        self.board = []
        self.winners = []
        self.won_pot = 0

    def clean_up(self):
        self.players = []
        self.sitting_out = []
        self.folded = []
        self.on_deck = []
        self.active = []
        self.deck = None
        self.stage = None
        self.pots = {}
        self.game_on = False
        self.th_start = False
        self.bet_to_call = 0
        self.dead_raise = False
        self.board = []
        self.winners = []
        self.won_pot = 0

    def is_game_over(self):
        num_of_players = len([p for p in self.players if p.chips > 0])
        if num_of_players < 2:
            return True

    def new_hand(self):
        self.players = [self.players[-1]] + self.players[:-1]
        if self.on_deck:
            self.players = self.players + self.on_deck
        self.on_deck = []
        self.folded = []
        self.active = [Hand(x) for x in list(self.players)]
        for hand in self.active:
            hand.act = False
        self.shuffle_and_deal()
        self.stage = 'Pre-Flop'
        self.pots = {}
        self.post_blinds()
        self.dead_raise = False
        self.winners = []
        self.won_pot = self.bb

    def next_stage(self):
        self.advance_stage()
        self.clear_line_bets()
        # move the blinds up front in the betting order if we're on
        # the flop turn or river.
        if self.stage in ['Flop', 'Turn', 'River']:
            # this will not do, because we have been rotating active and the order is not original.
            blinds = [x for x in self.active if x.player.name == self.players[-1].name or x.player.name == self.players[-2].name]
            for blind in blinds:
                self.active.remove(blind)
            if blinds:
                self.active = blinds + self.active
        for hand in self.active:
            self.act == None

    def rotate_active(self):
        """first to act is the first player in the active list, so we rotate
        that list after each turn."""
        if not self.active:
            return None
        elif len(self.active) == 1:
            return None
        else:
            self.active = [self.active[-1]] + self.active[:-1]

    def shuffle_and_deal(self):
        ranks = list('23456789TJQKA')
        suits = list('sdhc')
        self.deck = [x+y for x in ranks for y in suits]
        random.shuffle(self.deck)
        for hand in self.active:
            hand.cards.append(self.deck.pop(0))
            hand.cards.append(self.deck.pop(0))
        self.board = self.deck[:5]

    def deal_board(self, stage):
        if stage == 'Turn' or 'River':
            return [self.deck.pop(0)]
        else:
            return self.deck[:3]

    def __null_acts(self):
        for hand in self.active:
            hand.act = None
            self.bet_to_call = 0

    def advance_stage(self):
        if not self.stage:
            self.stage = 'Pre-Flop'
            self.__null_acts()
            return None
        if self.stage == 'Pre-Flop':
            self.stage = 'Flop'
            self.__null_acts()
            return None
        if self.stage == 'Flop':
            self.stage = 'Turn'
            self.__null_acts()
            return None
        if self.stage == 'Turn':
            self.stage = 'River'
            self.__null_acts()
            return None
        if self.stage == 'River':
            self.stage = None
            self.__null_acts()
            return None

    def add_player(self, name):
        p = Player(name, 1000)
        self.players.append(p)
        self.active.append(Hand(p))

    def get_hand_by_name(self,name):
        for hand in self.active:
            if hand.player.name == name:
                return hand

    def is_active(self, name):
        if self.active[0].player.name == name:
            return True

    def __every(self, lis, item):
        if item in lis and len(set(lis)) == 1:
            return True

    def is_hand_over(self):
        has_chips = [hand for hand in self.active if hand.player.chips > 0]
        if len(has_chips) <= 1:
            return True

    def is_stage_over(self):
        if len([h.act for h in self.active if h.act != None]) == len(self.active):
            return True

    ## Pot
    def add_to_pot(self, amt):
        if self.pots.keys():
            self.pots[max(self.pots.keys())]['amt'] += amt

    def clear_line_bets(self):
        while True:
            bets = [h.bet for h in self.active if h.bet > 0]
            if not bets:
                break
            elif len(bets) == 1:
                for hand in self.active:
                    if hand.bet > 0:
                        hand.player.chips += hand.bet
                        hand.bet = 0
            else:
                bet = min(bets)
                if self.pots.keys():
                    pot_key = max(self.pots.keys())+1
                else: pot_key = 1
                self.new_pot(pot_key)
                for hand in self.active:
                    if hand.bet > 0:
                        hand.bet -= bet
                        self.pots[pot_key]['amt'] += bet
                        self.pots[pot_key]['contenders'].append(hand)

    def new_pot(self,pot_key):
        self.pots.setdefault(pot_key, {'contenders': [], 'amt': 0, 'winners':[]})

    ## Player actions
    def all_in_bet(self, hand):
        hand.bet += hand.player.chips
        hand.player.chips = 0
        hand.all_in = True
        hand.act = 'bet'
        if hand.bet <= self.bet_to_call:
            hand.act = 'call'
        if not hand.bet >= 2 * self.bet_to_call:
            self.dead_raise = True
        if hand.bet > self.bet_to_call:
            self.bet_to_call = hand.bet

    def fold(self,hand):
        self.folded.append(hand)
        self.active.remove(hand)

    def call(self,hand):
        if hand.option == True:
            hand.option = False
        call_amt = self.bet_to_call - hand.bet
        if call_amt > hand.player.chips:
            self.all_in_bet(hand)
        elif call_amt == hand.player.chips:
            self.all_in_bet(hand)
        else:
            hand.player.chips -= call_amt
            hand.bet += call_amt
            hand.act = 'call'

    def bet(self, hand, allin=False, amt=None):
        for h in self.active:
            h.act = None
        if allin:
            self.all_in_bet(hand)
        else:
            hand.bet += amt
            hand.player.chips -= amt
            hand.act = 'bet'
            self.bet_to_call = hand.bet

    def post_blinds(self):
        sb = self.active[-2]
        bb = self.active[-1]
        bb.option = True
        sb.bet += self.sb
        sb.player.chips -= self.sb
        bb.bet += self.bb
        bb.player.chips -= self.bb
        bb.act = None
        sb.act = None
        self.bet_to_call = self.bb

    # Hand evaluation: eval_hands(), assign_winners_to_pots()
    def to_ranker(self,cards):
        res = [tuple(list(x)) for x in cards]
        return [ranker.convert(c) for c in res]

    def from_ranker(self,cards):
        return [''.join(ranker.convert(c)) for c in cards]

    def eval_hand(self,cards):
        cards = self.to_ranker(cards)
        res1 = ranker.main(cards)
        res2 = []
        for item in res1:
            if type(item) == type([1]):
                res2.append(self.from_ranker(item))
            else:
                res2.append(item)
        return res2

    def eval_hands(self):
        for hand in self.active:
            hand.hand_result = self.eval_hand(hand.cards + self.board)

    def get_winners(self,hands):
        lowest_score = 999
        for hand in hands:
            if hand.hand_result[1] < lowest_score:
                lowest_score = hand.hand_result[1]
        winners = [hand for hand in hands if hand.hand_result[1] == lowest_score]
        if len(winners) == 1:
            return winners
        elif len(winners) > 1:
            try:
                for hand in winners:
                    hand.kicker_val = self.eval_kickers(hand)[1]
                lowest_kicker_val = 999
                for hand in self.active:
                    if hand.kicker_val < lowest_kicker_val:
                        lowest_kicker_val = hand.kicker_val
                winners = [hand for hand in winners if hand.kicker_val == lowest_kicker_val]
                return winners
            except:
                return winners

    def eval_kickers(self,hand):
        if hand.hand_result[3]:
            self.eval_hand(hand.hand_result[3])

    def assign_winners_to_pots(self):
        pot_val = 0
        pot_keys = sorted(self.pots.keys(), reverse=True)
        for key in pot_keys:
            pot = self.pots[key]
            # what if this is None? i don't think it could be,
            # actually. for that to happen, the original all in better
            # would have to fold. but he cannot.
            eligible = [hand for hand in pot['contenders'] if hand in self.active]
            winners = self.get_winners(eligible)
            self.pots[key]['winners'] = winners
            self.winners += winners

    def payout(self):
        self.won_pot = self.sum_pots()
        for key in self.pots.keys():
            pot = self.pots[key]
            amt = pot['amt']
            num_of_players = len(pot['winners'])
            if amt % num_of_players == 0:
                for hand in pot['winners']:
                    hand.player.chips += amt / num_of_players
            else:
                remainder = amt % num_of_players
                amt -= remainder
                for hand in pot['winners']:
                    hand.player.chips += amt / num_of_players
                for x in range(remainder):
                    pot['winners'][x].player.chips += 1

    def get_table_for_display(self):
        table = []
        for player in self.players:
            for h in self.active:
                if h.player.name == player.name:
                    table.append(h.__repr__())
            for h in self.folded:
                if h.player.name == player.name:
                    table.append(h.player.name + ' ' + 'Folded')
        return table

    def get_game_info_for_display(self):
        if self.stage == 'Pre-Flop':
            return "Pot: %d, Bet to call: %d" % (self.sum_pots(), self.bet_to_call)
        elif self.stage == 'Flop':
            return "Pot: %d, Bet to call: %d, Board: %s" % (self.sum_pots(), self.bet_to_call, ' '.join(self.board[:3]))
        elif self.stage == 'Turn':
            return "Pot: %d, Bet to call: %d, Board: %s" % (self.sum_pots(), self.bet_to_call, ' '.join(self.board[:4]))
        elif self.stage == 'River':
            return "Pot: %d, Bet to call: %d, Board: %s" % (self.sum_pots(), self.bet_to_call, ' '.join(self.board[:5]))
        elif self.stage == None:
            return "Pot: 0, Bet to call: %d" % self.bet_to_call

    def sum_pots(self):
        psum = 0
        for pot in self.pots.keys():
            psum += self.pots[pot]['amt']
        return psum

class Hand:
    def __init__(self, player):
        self.player = player
        self.bet = 0
        self.cards = []
        self.act = None
        self.all_in = False
        self.hand_result = None
        self.kicker_val = 0
        self.option = False

    def __repr__(self):
        return self.player.name + ' ' + 'stack: ' + str(self.player.chips) + ' ' + 'bet: ' + str(self.bet)

dealer = Dealer()

# phenny commands
def tell_cards(phenny, input):
    for hand in dealer.active:
        phenny.write(['PRIVMSG', hand.player.name], 'Your hole cards: %s' % ' '.join(hand.cards))

def query_next(phenny, input):
    stage_over = dealer.is_stage_over()
    if not stage_over:
        next_up = dealer.active[0]
        for line in dealer.get_table_for_display():
            phenny.say("%s" % line)
        phenny.say("%s" % dealer.get_game_info_for_display())
        phenny.say("%s, you're up." % next_up.player.name)
    elif stage_over:
        dealer.advance_stage()
        dealer.clear_line_bets()
        if dealer.is_hand_over():
            dealer.eval_hands()
            dealer.assign_winners_to_pots()
            dealer.payout()
            announce(phenny, input)
            if not dealer.is_game_over():
                phenny.say("** Next Hand **")
                dealer.new_hand()
                tell_cards(phenny, input)
                query_next(phenny,input)
            else:
                phenny.say("The Game is Ended!")
                dealer.clean_up()
        elif dealer.stage:
            phenny.say("** %s **" % dealer.stage)
            query_next(phenny, input)
        else:
            dealer.eval_hands()
            dealer.assign_winners_to_pots()
            dealer.payout()
            announce(phenny, input)
            if not dealer.is_game_over():
                phenny.say("** Next Hand **")
                dealer.new_hand()
                tell_cards(phenny, input)
                query_next(phenny,input)
            else:
                phenny.say("The Game is Ended!")
                dealer.clean_up()

END_GAME = 0
ENDER = None
def th_quit_game(phenny, input):
    global ENDER
    if dealer.game_on:
        if dealer.is_active(input.nick):
            ENDER = input.nick
            phenny.say("%s has suggested ending the game. Another player must agree with the command: '.th-end-game-now" % input.nick)
th_quit_game.commands = ['th-quit-game']

def th_end_game_now(phenny, input):
    if dealer.game_on:
        if dealer.is_active(input.nick):
            if ENDER != input.nick:
                phenny.say("Texas Holdem is finished!")
                dealer.clean_up()
th_end_game_now.commands = ['th-end-game-now']

def announce(phenny, input):
    won_pot = dealer.sum_pots()
    winners = set(dealer.winners)
    phenny.say("The winners are: ")
    for hand in winners:
        hand_result = None
        if hand.hand_result[3]:
            hand_result = ' '.join(hand.hand_result[2] + hand.hand_result[3])
        else:
            hand_result = ' '.join(hand.hand_result[2])
        phenny.say("%s holding %s  Stack: %d  %s" % (hand.player.name, ' '.join(hand.cards), hand.player.chips, hand_result))

def th_challenge(phenny, input):
    if dealer.game_on == 1:
        pass
    else:
        dealer.game_on = 1
        dealer.add_player(input.nick)
        phenny.say("%s has started a game of Texas Holdem! Who's in?" % input.nick)
th_challenge.commands = ['th!', 'th']

def th_join(phenny, input):
    if dealer.game_on == 1:
        phenny.say("%s has joined Texas Holdem! Who else?"  % input.nick)
        dealer.add_player(input.nick)
    else:
        phenny.say("%s, there is no game of Holdem to join." % input.nick)
th_join.commands = ['hjoin!', 'hjoin', 'thjoin!', 'thjoin']

def th_start(phenny, input):
    if not dealer.th_start:
        dealer.th_start = True
        if len(dealer.players) < 2:
            phenny.say("We don't have enough players yet.")
            dealer.th_start = False
            return
        if dealer.game_on:
            phenny.say("Welcome to Texas Holdem!")
            dealer.new_hand()
            phenny.say("** %s **" % dealer.stage)
            tell_cards(phenny, input)
            query_next(phenny, input)
        else:
            phenny.say("%s, there is no active Holdem game." % input.nick)
    else:
        pass
th_start.commands = ['th-start', 'hstart', 'tstart']

def th_fold(phenny, input):
    if dealer.game_on:
        if dealer.is_active(input.nick):
            dealer.fold(dealer.get_hand_by_name(input.nick))
            phenny.say("%s has folded." % input.nick)
            dealer.rotate_active()
            query_next(phenny, input)
        else:
            phenny.say("%s, it isn't your turn!" % input.nick)
    else:
        phenn.say("%s, there is no active Holdem game." % input.nick)
th_fold.commands = ['fold']

def th_call(phenny, input):
    if dealer.game_on:
        if dealer.is_active(input.nick):
            h = dealer.get_hand_by_name(input.nick)
            dealer.call(h)
            phenny.say("%s has called." % input.nick)
            dealer.rotate_active()
            query_next(phenny,input)
        else:
            phenny.say("%s, it isn't your turn!" % input.nick)
    else:
        phenn.say("%s, there is no active Holdem game." % input.nick)
th_call.commands = ['call']

def th_bet(phenny, input):
    if dealer.game_on:
        if dealer.is_active(input.nick):
            h = dealer.get_hand_by_name(input.nick)
            try:
                bet = int(input.group(2))
            except:
                phenny.say("%s, there was something defective about your command. Try again." % input.nick)
            if bet == h.player.chips:
                dealer.all_in_bet(h)
                phenny.say("%s is all in!" % input.nick)
                dealer.rotate_active()
                query_next(phenny, input)
            elif bet > h.player.chips:
                phenny.say("%s, you don't have enough chips to make that bet. Try again." % input.nick)
            elif bet < dealer.bb:
                phenny.say("The minium bet is %d" % dealer.bb)
            elif dealer.bet_to_call > 0:
                phenny.say("%s, there has already been a bet. You should fold, call or raise." % input.nick)
            else:
                phenny.say("bettor: %s" % h.__repr__())
                dealer.bet(h, amt=bet)
                dealer.rotate_active()
                phenny.say("%s has bet %d!" % (input.nick, bet))
                query_next(phenny,input)
        else:
            phenny.say("%s, it isn't your turn!" % input.nick)
    else:
        phenn.say("%s, there is no active Holdem game." % input.nick)
th_bet.commands = ['hbet']

def th_raise(phenny, input):
    if dealer.game_on:
        if dealer.is_active(input.nick):
            try:
                amount = int(input.group(2))
            except:
                print "problem in int"
            h = dealer.get_hand_by_name(input.nick)
            if dealer.dead_raise:
                phenny.say("%s, you cannot raise that bet. Call or Fold." % input.nick)
            elif not amount + h.bet >= 2 * dealer.bet_to_call:
                if h.bet == h.player.chips:
                    dealer.all_in_bet(h)
                    phenny.say("%s is all in!" % input.nick)
                    dealer.rotate_active()
                    query_next(phenny, input)
                else:
                    phenny.say("%s, your raise is too small." % input.nick)
            elif amount > h.player.chips:
                phenny.say("%s, you don't have enough chips to place that bet" % input.nick)
            elif amount == h.player.chips:
                dealer.bet(h, allin=True, amt=amount)
                phenny.say("%s is all in!" % input.nick)
                dealer.rotate_active()
                query_next(phenny, input)
            else:
                phenny.say("raiser: %s" % h.__repr__()) # this is correct
                dealer.bet(h, allin=False, amt=amount)
                phenny.say("%s has raised the bet to %d!" % (input.nick, dealer.bet_to_call))
                dealer.rotate_active()
                query_next(phenny, input)
            # except:
            #     phenny.say("%s, there was something defective about your bet. Try again!" % input.nick)
        else:
            phenny.say("%s, it isn't your turn!" % input.nick)
    else:
        phenny.say("%s, there is no active Holdem game." % input.nick)
th_raise.commands = ['raise!', 'raise']

def th_allin(phenny, input):
    if dealer.game_on:
        if dealer.is_active(input.nick):
            hand = dealer.get_hand_by_name(input.nick)
            dealer.bet(hand, allin=True, amt=hand.player.chips)
            phenny.say("%s is all in!" % input.nick)
            dealer.rotate_active()
            query_next(phenny,input)
        else:
            phenny.say("%s, it isn't your turn!" % input.nick)
    else:
        phenn.say("%s, there is no active Holdem game." % input.nick)
th_allin.commands = ['allin']

def th_check(phenny, input):
    if dealer.game_on:
        if dealer.is_active(input.nick):
            phenny.say("%s checks." % input.nick)
            dealer.get_hand_by_name(input.nick).act = 'check'
            dealer.get_hand_by_name(input.nick).option = False
            dealer.rotate_active()
            query_next(phenny,input)
        else:
            phenny.say("%s, it isn't your turn!" % input.nick)
    else:
        phenn.say("%s, there is no active Holdem game." % input.nick)
th_check.commands = ['check']

if __name__ == '__main__':
    print __doc__
