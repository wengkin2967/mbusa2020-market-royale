import Command
from Map import Map
from BasePlayer import BasePlayer
import Market
import heapq as hq
import copy
from Priority_q_node import pq_node
from math import sqrt
from Market import PRODUCTS
from Game import *
import time
import random
from collections import defaultdict

UNKNOW = None

class Player(BasePlayer):
    def __init__(self, mode='MAX', max_depth=50, interest=0.1, max_buy=10, risk_attitude=0.3):
        super().__init__()

        # Records information about markets visited, includes price and amounts
        self.market_visited_info = {}

        # Tracker of info gained from other players (only product amount), will be regularly updated.
        self.player_info = {}

        # List of markets researched
        self.researched_markets = []

        # {product : (amount,price)}
        self.inventory_tracker = {}

        # Keep Track of turn number (might not be used)
        self.turn_tracker = 0

        self.interest = interest
        self.risk_attitude = risk_attitude

        self.current_loc = None
        self.loc = None 
        self.this_market = None 
        self.all_product_info = {}
        self.black_markets = None
        self.grey_markets = None

        self.next_best_move = None
        self.start_time = None

        self.current_best_aim = []

    def take_turn(self, loc, this_market, info, black_markets, grey_markets):
        """@param loc Name of your current location on map as a str.
           @param this_market A dictionary {product:(price,amount)} of prices and amounts 
                              at this market (if you have researched, {} otherwise).
           @param info A dictionary {market:{product:price}} of information gleaned from other 
                       players that were here when you arrived.
           @param black_markets A list of market names (strings) that are Black.
           @param grey_markets A list of market names (strings) that are Grey.

           @return (cmd, data) cmd is one of Command.* and data is a tuple of necessary data for a command.
        """
        self.start_time = time.perf_counter()
        self.turn_tracker += 1
        assert(type(loc) is str)
        assert(type(this_market) is dict)
        assert(type(info) is dict)
        self.current_loc = loc
        self.loc = loc
        self.this_market = this_market 
        self.info = info
        self.black_markets = black_markets
        self.grey_markets = grey_markets
        self.next_best_move = (Command.RESEARCH, None)
        self.highest_score = None
        
        # updating information
        for market, information in info.items():
            if market not in self.all_product_info:
                information = {product:(price, UNKNOW) for product, price in information.items()}
                self.all_product_info[market] = information
        if this_market:
            self.all_product_info[loc] = copy.deepcopy(this_market)
        #print(self.all_product_info)


        #return (Command.RESEARCH, None)
        #print(random.choice(self.map.get_neighbours(loc)))
        
        self.mode_decision()
        #return (Command.MOVE_TO, random.choice(list(self.map.get_neighbours(loc))))
        print(self.next_best_move)
        #print(self.current_best_aim)
        return self.next_best_move

    def goals_not_achieved(self):
        """
        Helper to return all goals not yet achieved.
        """
        return [goal for goal in self.goal.keys() if not self.goal_met(goal)]
    
    def goal_met(self, goal_item):
        """
        Helper to check whether a goal item has been achieved.
        """
        return self.inventory_tracker.get(goal_item,(0,0))[0] >= \
                    self.goal[goal_item]
    
    def mode_decision(self):
        if len(self.goals_not_achieved()) > 0:
            self.goal_mode()
        else:
            self.arbitrage()


    def goal_mode(self):
        self.search_best_aim()
        if len(self.current_best_aim) == 0:
            self.next_best_move = (Command.RESEARCH, None)
            return
        if self.current_best_aim[0][0] > 0:
            self.next_best_move = (Command.PASS, None)
            return
        if self.current_best_aim[0][-1] is True:
            if self.loc in self.researched_markets:
                self.next_best_move = (Command.BUY, (self.current_best_aim[0][2], self.current_best_aim[0][4]))
                self.buy_item(self.current_best_aim[0][2], self.current_best_aim[0][4],self.current_best_aim[0][3])
                return
            else:
                self.next_best_move = (Command.RESEARCH, None)
                self.researched_markets.append(self.loc)
                return
        else:
            self.next_best_move = (Command.MOVE_TO, self.current_best_aim[0][-1][1])


    
    def search_best_aim(self):
        #print(self.goals_not_achieved())
        self.current_best_aim = []
        
        for goal_item in self.goals_not_achieved():
            lacking = self.goal[goal_item] - self.inventory_tracker.get(goal_item,(0,0))[0] 
            for market, information in self.all_product_info.items():
                #print(information)
                revenue = GOAL_BONUS
                if information[goal_item][1] is None:
                    pass
                elif information[goal_item][1] < lacking:
                    revenue = GOAL_BONUS / lacking
                    lacking = information[goal_item][1]
                    revenue = revenue * lacking
                direct_cost = (information[goal_item][0] * lacking)
                undirect_cost = 0

                path = self.shortest_path(self.loc, market)
                if (path is not True) and (market in self.black_markets or market in self.grey_markets):
                    undirect_cost = OUTSIDE_CIRCLE_PENALTY * (len(path)/2)

                current_profit = revenue - direct_cost - undirect_cost
                self.current_best_aim.append((-current_profit, market, goal_item, information[goal_item][0] ,lacking ,path))
        
        self.current_best_aim.sort()
        #print(self.current_best_aim)


        '''
        for market, information in self.info.items():
            for goal in self.goals_not_achieved():
                if goal not in self.current_best_price and information[1] > 0:
                    # {goal: (market_id, price, avaliable amount)}
                    self.current_best_price[goal] = (market, information[0], information[1])
                elif goal in self.current_best_price and information[1] > 0:
                    if information()'''


    # from binxing
    def shortest_path(self, location_1, location_2):
        """
        Finds shortest path between any location and centrenode using BFS
        """
        graph = self.map.map_data['node_graph']
        #keeps track of explored nodes
        explored = []
        #keeps track of all paths to be checked
        queue = [[location_1]]
        if location_2 == location_1:
            return True
        # loops until all possible paths are checked
        while queue:
            #pop first path from queue
            path = queue.pop(0)
            #gets last node from the path
            node = path[-1]
            if node not in explored:
                neighbours = graph[node]
                #go through all neighbournodes, construct new path
                #and push to queue
                for neighbour in neighbours:
                    new_path  = list(path)
                    new_path.append(neighbour)
                    queue.append(new_path)
                    #return path if neighbour is centrenode
                    if neighbour == location_2:
                        return new_path
                explored.append(node)
    
    def arbitrage(self):
        self.search_best_arbitrage()
        if len(self.current_best_aim) == 0:
            self.next_best_move = (Command.RESEARCH, None)
            return
        if self.current_best_aim[0][0] > 0:
            # need to make a escape mode to go to centre
            self.next_best_move = (Command.PASS, None)
            return
        if self.current_best_aim[0][-1] is True:
            if self.loc in self.researched_markets:
                self.next_best_move = (Command.BUY, (self.current_best_aim[0][2], self.current_best_aim[0][4]))
                self.buy_item(self.current_best_aim[0][2], self.current_best_aim[0][4],self.current_best_aim[0][3])
                return
            else:
                self.next_best_move = (Command.RESEARCH, None)
                self.researched_markets.append(self.loc)
                return
        else:
            self.next_best_move = (Command.MOVE_TO, self.current_best_aim[0][-1][1])
            

    

    def search_best_arbitrage(self):
        #print(self.goals_not_achieved())
        self.current_best_aim = []
        total_known_amount = defaultdict(int)
        avg_amount = {}
        market_counter = 0
        for market, information in self.all_product_info.items():
            if market in self.researched_markets:
                for item in PRODUCTS:
                    market_counter += 1
                    total_known_amount[item] += information[item][1]
        for item in PRODUCTS:
            avg_amount[item] = total_known_amount[item] / market_counter

        for item in PRODUCTS:
            for market_1, information_1 in self.all_product_info.items():
                for market_2, information_2 in self.all_product_info.items():
                    if market_1 == market_2:
                        continue
                    #print(information)
                    price_1 = information_1[item][0]
                    price_2 = information_2[item][0]
                    if price_1 < price_2:
                        amount = information_1[item][1]
                        if amount is not None and amount == 0:
                            continue
                        if amount is None:
                            amount = avg_amount[item]
                        
                        max_amount = (self.risk_attitude * self.gold)//price_1
                        amount = min(amount, max_amount)

                        revenue = amount * (price_2 - price_1)
                        path_before_arbitrage = self.shortest_path(self.loc, market_1)
                        path_arbitrage = self.shortest_path(market_1, market_2)
                        
                        undirect_cost = 0
                        if (path_before_arbitrage is not True) and \
                            (market_1 in self.black_markets or \
                                market_1 in self.grey_markets):
                            undirect_cost += OUTSIDE_CIRCLE_PENALTY * (len(path_before_arbitrage)/2)
                        
                        if (path_arbitrage is not True) and \
                            (market_2 in self.black_markets or \
                                market_2 in self.grey_markets):
                            undirect_cost += OUTSIDE_CIRCLE_PENALTY * (len(path_arbitrage)/2)
                        revenue -= undirect_cost
                        self.current_best_aim.append((-revenue, market_1, item, information_1[item][0] ,amount ,path_before_arbitrage))
        
        self.current_best_aim.sort()
        #print(self.current_best_aim)

    def buy_item(self,item,item_amount,price):
            """
            Helper to buy an item, item_amount times
            """
            self.inventory_tracker[item] =  (self.inventory_tracker.get(item,(0,0))[0] + item_amount, price)
            self.gold -= item_amount * price





if __name__ == "__main__":

    #from Player import Player
    from kin import Player as P2
    g = Game([Player(),P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2()], verbose=False)
    res = g.run_game()
    print(res)
