"""
Player IDs are ints 1...N
Map locations are str names.
"""
import random
import time
import Command
from BasePlayer import BasePlayer
from Market import *
from Map import Map
import copy
import string
import traceback

NUM_TURNS = 50

START_GOLD = sum([sum(P_BOUNDS[k])/2 * sum(A_BOUNDS[k])/2 for k in PRODUCTS])

GOAL_BONUS = 10000

OUTSIDE_CIRCLE_PENALTY = 100  # gold per turn outside circle

EXCHANGE_LENGTH = 3   # number of markets to exchange information upon from each co-located player

    # Indexes into player tuple
INFO_LOC = 0   # location str
INFO_N   = 1   # number of turns at this location (int)
INFO_OBJ = 2   # Player object (as supplied by student)
INFO_INV = 3   # player inventory (dictionary keyed by product and INV_GOLD)
INFO_HISTORY = 4   # player visit list (list of node names researched in order)
INFO_GOAL = 5   # goal set for player at start of game

    # indexes into Inventory
INV_GOLD = 'Gold'

MSG_NO_RESEARCH = "You have not researched this market"

class Game:
    def __init__(self, player_list, verbose=False, interest_rate=0.10):
        """ @param player_list List of Player objects 
            @param interest_rate is in range [0,1]
        """
        self.verbose = verbose

        map_width = 200 # Dimensions of map
        map_height = 100
        resolution_x = 2 # Resolution to render the map at
        resolution_y = 3

        # Game using the simple small map.
        # node_list = ["Academy", "City", "Gallery", "Junkyard", "Office", "Park", "Stadium", "Tree", "Weather Station"]
        # self.map = Map(node_list, map_width, map_height, resolution_x, resolution_y, seed=2354)

        # Game using a medium map.
        node_list = list(string.ascii_uppercase)
        self.map = Map(node_list, map_width, map_height, resolution_x, resolution_y, seed=23624)

        # Game using a large map.
        #node_list = list(string.ascii_uppercase) + list(string.ascii_lowercase)
        #self.map = Map(node_list, map_width, map_height, resolution_x, resolution_y, seed=2360)

        random.seed(time.time())
        self.markets = {node:Market() for node in self.map.get_node_names()}  # need to randomise markets params BUG!

        self.have_researched = {node:[] for node in self.map.get_node_names()}  # list of player ids that hace researched this node

        self.turn_num = 0
        self.num_players = 0           # next player id is this + 1
        self.players = {}              # key=integer index into player_list  value=tuple indexed by INFO_*

        self.interest = interest_rate

        for p in player_list:
            self.add_player(p)

    def add_player(self, p):
        """Random location on the current outer circle, empty inventory.
        """
        assert(isinstance(p, BasePlayer))
            #stackoverflow.com/questions/34439/finding-what-methods-a-python-object-has
            #stackoverflow.com/questions/610883/how-to-know-if-an-object-has-an-attribute-in-python
        assert("take_turn" in [n for n in dir(p) if callable(getattr(p, n))])
        assert("set_gold" in [n for n in dir(p) if callable(getattr(p, n))])
        assert("set_goal" in [n for n in dir(p) if callable(getattr(p, n))])
        assert("set_map" in [n for n in dir(p) if callable(getattr(p, n))])

        start_loc = random.choice(list(self.map.get_node_names()))
        start_inv = {k:0 for k in PRODUCTS}
        start_inv[INV_GOLD] = START_GOLD

        goal = {k:random.randint(v[0],v[1]) for k,v in A_BOUNDS.items()}

        self.players[self.num_players + 1] = {INFO_LOC:start_loc, INFO_N:0, INFO_OBJ:p, INFO_INV:start_inv, 
                                              INFO_HISTORY:[], INFO_GOAL:copy.copy(goal)}
        self.num_players += 1

        p.set_goal(goal)
        p.set_gold(float(START_GOLD))
        p.set_map(copy.deepcopy(self.map))


    def get_prices_from_other_players(self, p_id):
        """@return Dictionary node:price_dict, where price_dict = {product:price} as str:float
        """
        players_here = [p_info for p_id,p_info in self.players.items() if p_info[INFO_LOC] == self.players[p_id][INFO_LOC]]

        ret_value = {}
        for p_info in players_here:
            hist = p_info[INFO_HISTORY]
            if len(hist) > 0:
                indexes = [-1] + random.sample(range(len(hist)-1), min(EXCHANGE_LENGTH, len(hist)-1))  # n=0 is ok
                for i in indexes:
                    ret_value[hist[i]] = self.markets[hist[i]].get_prices()

        return ret_value

    def game_result(self):
        """For each player, determine their final score.    
           @return List of scores in same order as players list.
        """
        score = []
        for p_id,p_info in self.players.items():
            met_goals = [p_info[INFO_INV][prod] >= amount for prod,amount in p_info[INFO_GOAL].items()]
            s = GOAL_BONUS * sum(met_goals) + p_info[INFO_INV][INV_GOLD]

            score.append(s)

        return score

    def run_game(self, num_turns=NUM_TURNS):
        """For each turn, shuffle players and call the take_turn(...).

           @return List of scores in order players sent to constructuor.
           @return Tuple (player object, error message)
        """

        for turns in range(num_turns):
            self.turn_num += 1

            self.map.move_circle(num_turns)

            node_status = self.map.get_node_status()
            bnodes = [name for name, status in node_status if status == Map.NODE_STATUS_BLACK]
            gnodes = [name for name, status in node_status if status == Map.NODE_STATUS_GREY]

            temp = list(self.players.items())
            random.shuffle(temp)
            for p_id,p_info in temp:

                if self.verbose:
                    self.map.render_map()
                    self.map.pretty_print_map()

                msg = []

                if p_info[INFO_INV][INV_GOLD] < 0:
                    i = round(-self.interest * p_info[INFO_INV][INV_GOLD])
                    msg.append("Interest of {} charged.".format(i))
                    p_info[INFO_INV][INV_GOLD] -= i

                if self.map.outside_circle(p_info[INFO_LOC]):
                    msg.append("Outside circle charge {}".format(OUTSIDE_CIRCLE_PENALTY))
                    p_info[INFO_INV][INV_GOLD] -= OUTSIDE_CIRCLE_PENALTY
                    
                other_info = {}
                if p_info[INFO_N] == 0:
                    other_info = self.get_prices_from_other_players(p_id)
                p_info[INFO_N] += 1

                market = self.markets[p_info[INFO_LOC]]

                if p_id in self.have_researched[p_info[INFO_LOC]]:
                    this_market = copy.deepcopy(market.get_price_amount())
                else:
                    this_market = {}

                try:
                    cmd,data = p_info[INFO_OBJ].take_turn(p_info[INFO_LOC], this_market, copy.deepcopy(other_info), bnodes, gnodes)
                except Exception:
                    return((p_info[INFO_OBJ], traceback.format_exc()))

                if cmd == Command.MOVE_TO:
                    assert(type(data) is str)
                    if self.map.is_road(p_info[INFO_LOC], data):
                        msg.append("Moved from {} to {}".format(p_info[INFO_LOC], data))
                        p_info[INFO_LOC] = data
                        p_info[INFO_N] = 0  # no turns in new location
                    else:
                        msg.append("No Move: {} is not connected to {}".format(data, p_info[INFO_LOC]))
                elif cmd == Command.BUY:
                    if p_id not in self.have_researched[p_info[INFO_LOC]]:
                        msg.append(MSG_NO_RESEARCH)
                    else:
                        if p_info[INFO_INV][INV_GOLD] < 0:
                            msg.append("Not enough gold to buy anything.")
                        else:
                            assert(len(data) == 2)
                            data = list(data)
                            prod,am,cost = market.sell(*data)
                            p_info[INFO_INV][prod] += am
                            p_info[INFO_INV][INV_GOLD] -= cost
                            msg.append("Bought {} {}".format(am, prod))
                elif cmd == Command.SELL:
                    if p_id not in self.have_researched[p_info[INFO_LOC]]:
                        msg.append(MSG_NO_RESEARCH)
                    else:
                        assert(len(data) == 2)
                        data = list(data)
                        assert(data[0] in PRODUCTS)
                        assert(type(data[1]) is int)
                        data[1] = min(p_info[INFO_INV][data[0]], data[1])  # cannot sell mmore than own
                        prod,am,cost = market.buy(*data)
                        p_info[INFO_INV][prod] -= am
                        p_info[INFO_INV][INV_GOLD] += cost
                        msg.append("Sold {} {}".format(am, prod))
                elif cmd == Command.RESEARCH:
                    p_info[INFO_HISTORY].append(p_info[INFO_LOC])
                    msg.append("Researched at {}".format(p_info[INFO_LOC]))
                    self.have_researched[p_info[INFO_LOC]].append(p_id)

                if self.verbose:
                    print("{} {}".format(p_id, msg))
            if self.verbose:
                print(self)

        return self.game_result()

    def __repr__(self):
        s = "Game: num_players={} turn_num={:4d}\n".format(self.num_players, self.turn_num)

        bar  = "-" * len(s) + "\n"
        s += bar
        
        for p in self.players.values():
            s += "loc={:20s}, N={:3d}, Inv={}\n".format(p[INFO_LOC], p[INFO_N], p[INFO_INV])

        s += bar
        for node,m in self.markets.items():
            s += "{:20s}: ".format(node)
            ps = m.get_prices()  # dict with product:price
            for prod in ps:
                am = m.amounts[prod]
                s += "{}:{:5d} ".format(prod, am)
            s += "\n"

        s += "\n\n"

        return s


if __name__ == "__main__":

    from Player import Player

    g = Game([Player()], verbose=True)
    res = g.run_game()
    print(res)
