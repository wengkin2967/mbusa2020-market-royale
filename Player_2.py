import Command
from Map import Map
from BasePlayer import BasePlayer
import Market
import heapq as hq
import copy
#from Priority_q_node import pq_node
from math import sqrt
from Market import PRODUCTS
from Game import *
import time
import random
from collections import defaultdict
import pdb

UNKNOW = None

class Player(BasePlayer):
    def __init__(self, mode='MAX', max_depth=50, interest=0.1, max_buy=10, risk_attitude=1, max_turn=300):
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
        self.max_turn = max_turn

        self.current_loc = None
        self.loc = None 
        self.this_market = None 
        self.all_product_info = {}
        self.black_markets = None
        self.grey_markets = None

        self.next_best_move = None
        self.start_time = None

        self.current_best_aim = []
        self.goal_copy = None
        self.first_time = True

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
        #print(black_markets)
        #print(self.gold)
        if False and self.gold < 0:
            i = -self.interest * self.gold
            self.gold -= i
            print(f"----------------------negative gold: {self.gold}")

        # track black market loss
        if False and self.loc in black_markets:
            self.gold -= 100
            print('-----------------------black market')
        
        if(self.turn_tracker == 299 and self.gold < 100):
            pdb.set_trace()
        
        # This part of code is used for the robot to arbitrage at first 60% turns
        if True and self.first_time:
            self.first_time = False
            self.goal_copy = copy.deepcopy(self.goal)
            for item in self.goal.keys():
                self.goal[item] = 0 
        if self.turn_tracker > 0.6 * self.max_turn:
            self.goal = copy.deepcopy(self.goal_copy)
        
        # abandon those target cannot meet
        elif self.turn_tracker > 0.85 * self.max_turn:
            useless_items = self.goals_not_achieved()
            for i in useless_items:
                self.goal[i] = 0
        
        else:
            # make sure in the first 60 % research as much as market as possible
            if self.loc not in self.researched_markets:
                self.researched_markets.append(self.loc)
                self.next_best_move = (Command.RESEARCH, None)
                #print(self.next_best_move)
                return self.next_best_move

        # this code is just aim for printing information
        if False and self.turn_tracker == 299:
            print('------------')
            print(self.goal_copy)
            print(self.inventory_tracker)
            print(self.gold)
            print('------------')

        # updating information from current market and other market (from competitor data)
        for market, information in info.items():
            if market not in self.all_product_info:
                information = {product:(price, UNKNOW) for product, price in information.items()}
                self.all_product_info[market] = information
        if this_market:
            self.all_product_info[loc] = copy.deepcopy(this_market)
        
        
        
        # make sure in the first 2.5 % round just researching market.
        # avoid if there is too less information and do wrong decision
        if True and self.turn_tracker < self.max_turn * 0.025:
            if self.loc not in self.researched_markets:
                self.researched_markets.append(self.loc)
                self.next_best_move = (Command.RESEARCH, None)
                #print(self.next_best_move)
                return self.next_best_move
            potential_node = [i for i in list(self.map.get_neighbours(loc)) if i not in self.researched_markets]
            self.next_best_move = (Command.MOVE_TO, random.choice(potential_node))
            #print(self.next_best_move)
            return self.next_best_move
        
        # main method, used to decided the action;
        # this method will modify self.next_best_action for return
        self.mode_decision()
        #print(self.next_best_move)
        return self.next_best_move

    # code from kin
    def goals_not_achieved(self):
        """
        Helper to return all goals not yet achieved.
        """
        return [goal for goal in self.goal.keys() if not self.goal_met(goal)]
    
    # code from kin
    def goal_met(self, goal_item):
        """
        Helper to check whether a goal item has been achieved.
        """
        return self.inventory_tracker.get(goal_item,(0,0))[0] >= \
                    self.goal[goal_item]

    # code modify based on kin's code
    def excess_item(self):
        """
        Helper to return all goals not yet achieved.
        """
        return [goal for goal in self.goal.keys() if self.excess_or_not(goal)]
    
    # code modify based on kin's code
    def excess_or_not(self, goal_item):
        """
        Helper to check whether a goal item has been achieved.
        """
        return self.inventory_tracker.get(goal_item,(0,0))[0] > \
                    self.goal[goal_item]
    
    def mode_decision(self):
        """
        This method is based on the current situation to
        1. buy for meeting the goal
        2. arbitrage buying
        3. arbitrage selling

        eventually it will modify self.next_best_move for return to game
        """
        self.current_best_aim = []
        
        # useless code
        if False:
            #print('--------')
            self.search_best_aim()
            self.search_best_arbitrage()
                
            try:
                sell_or_not = self.current_best_aim[0]
                self.selling_mode()
                
                if self.current_best_aim[0] == sell_or_not:
                    self.get_move(mode='SELL')
                else:
                    self.get_move()
            except Exception as e:
                self.get_move()
                #print(self.current_best_aim)
                #print('Exception error')
                #print(e)
            return None


        # if we do not meet the goal, try to buy something to meet the goal
        if len(self.goals_not_achieved()) > 0 and self.turn_tracker <= int(self.max_turn * 0.97):
            self.search_best_aim()
            self.get_move()
            return
        # if we already meet the gold or gold is 0 (first 60% turns)
        # we start to arbitrage
        if (len(self.excess_item()) == 0 or (len(self.goals_not_achieved()) > 0 and self.current_best_aim[0][0]>0))\
             and self.turn_tracker <= int(self.max_turn * 0.97):
            self.search_best_arbitrage()
            try:
                if (self.current_best_aim[0][0] < 0):
                    self.get_move()
                    return
            except:
                pass
        # if we have buy something from the arbitrage buying process
        # we will sell those things at a higest price
        if len(self.excess_item()) > 0 and self.turn_tracker <= int(self.max_turn * 0.97):
            self.selling_mode()
            self.get_move(mode='SELL')
            return
        
        
        # if we have no purpose (goal met and no arbitrage and at the end 5% of turns)
        # try to walk to the middle avoid balck/gray area
        centre = self.centrenode()
        path = self.shortest_path(self.loc, centre)
        #print(f'escape: from {self.loc} to {path}')
        if path is not True:
            self.next_best_move = (Command.MOVE_TO, path[1])
        else:
            self.next_best_move = (Command.PASS, None)



    # code from binxing
    def centrenode(self): 
        """
        Finds centrenode based mapwidth and mapheight
        """
        targetnodelist = []
        mapheight = (self.map.map_height)/2
        mapwidth = (self.map.map_width)/2
        for node, coordinates in self.map.map_data['node_positions'].items():
            x, y, circlestatus = coordinates
            x_abs = abs(mapwidth - x)
            y_abs = abs(mapheight - y)
            if node not in self.black_markets or node not in self.grey_markets:
                targetnodelist.append([node, x_abs + y_abs])
        return sorted (targetnodelist, key = lambda node: node[1])[0][0]
    
    def selling_mode(self):
        """
        This code is trying to find the best offer price that we could sell
        our excess products
        """

        # check every item
        for item in self.excess_item():
            # check if there is any excess item
            excess = self.inventory_tracker.get(item,(0,0))[0] - self.goal[item]
            
            # if there is no excess, do nothing
            if excess <= 0:
                continue
            # start to find the best market
            for market, information in self.all_product_info.items():
                # based on price to check the selling profits
                price = information[item][0]
                revenue = price * excess
                undirect_cost = 0
                path = self.shortest_path(self.loc, market)
                # add balck market arbitrage buying to reduce revenue
                if type(path) == list:
                    for i in path:
                        if i in self.black_markets or i in self.grey_markets:
                            undirect_cost += OUTSIDE_CIRCLE_PENALTY 

                # append for ranking to decide best action
                current_profit = revenue - undirect_cost
                self.current_best_aim.append((-current_profit, market, item, information[item][0] ,excess ,path))
        # ranking for decdiding best action
        self.current_best_aim.sort()

    def get_move(self, mode='BUY'):
        """
        based on the ranking of our aim,
        find out the best one
        and assign it to our self.next_best_move
        """
        # if it is the first turn, there will be noting to do, just research
        if len(self.current_best_aim) == 0:
            self.next_best_move = (Command.RESEARCH, None)
            self.researched_markets.append(self.loc)
            return
        # if there is no good action, just do nothing
        if self.current_best_aim[0][0] > 0:
            self.next_best_move = (Command.PASS, None)
            return
        # if there is profit avaliable to obtain
        if self.current_best_aim[0][-1] is True:
            # if we do not research the current best offer market yet
            # resarch
            if self.loc in self.researched_markets:
                # buying
                if mode == 'BUY':
                    self.next_best_move = (Command.BUY, (self.current_best_aim[0][2], self.current_best_aim[0][4]))
                    self.buy_item(self.current_best_aim[0][2], self.current_best_aim[0][4],self.current_best_aim[0][3])
                    return
                # selling
                if mode == 'SELL':
                    self.next_best_move = (Command.SELL, (self.current_best_aim[0][2], self.current_best_aim[0][4]))
                    self.sell_item(self.current_best_aim[0][2], self.current_best_aim[0][4],self.current_best_aim[0][3])
                    return
            # research
            else:
                self.next_best_move = (Command.RESEARCH, None)
                self.researched_markets.append(self.loc)
                return
        # if we not reach our aim yet, we keep moving
        else:
            self.next_best_move = (Command.MOVE_TO, self.current_best_aim[0][-1][1])


    
    def search_best_aim(self):
        """
        This method is aiming to find the best price for us to meet our goal
        """
        
        for goal_item in self.goals_not_achieved():
            for market, information in self.all_product_info.items():
                # find out what is not enough
                lacking = self.goal[goal_item] - self.inventory_tracker.get(goal_item,(0,0))[0] 
                revenue = GOAL_BONUS
                # if there is no item avaliable, give up this market
                if information[goal_item][1] == 0:
                    continue
                # if we do not research the market yet, we make just make an 
                # assumption that there is enough item for buying
                if information[goal_item][1] is None:
                    pass
                # if there is low amount, we just buy the avaliable
                elif information[goal_item][1] < lacking:
                    
                    #print('-------------------')
                    revenue = GOAL_BONUS / lacking
                    lacking = information[goal_item][1]
                    revenue = revenue * lacking
                # calculate the purchasing cost
                direct_cost = (information[goal_item][0] * lacking)
                undirect_cost = 0

                # account for the punishment from black market
                path = self.shortest_path(self.loc, market)


                if type(path) == list:
                    for i in path:
                        if i in self.black_markets or i in self.grey_markets:
                            undirect_cost += OUTSIDE_CIRCLE_PENALTY 

                #if (path is not True) and (market in self.black_markets or market in self.grey_markets):
                #    undirect_cost = OUTSIDE_CIRCLE_PENALTY * (len(path)/2)

                # based on the net profit to rank those aims
                current_profit = revenue - direct_cost - undirect_cost
                self.current_best_aim.append((-current_profit, market, goal_item, information[goal_item][0] ,lacking ,path))
        # rank those avaliable option
        self.current_best_aim.sort()


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
            
    def search_best_arbitrage(self):
        """
        This method is aming to find the best offer price and selling price
        in the map, so that we can arbitrage and make profit
        """
        # make an assumption about the avaliable amount of item in those
        # market which is not research yet
        total_known_amount = defaultdict(int)
        avg_amount = {}
        market_counter = 0
        for market, information in self.all_product_info.items():
            if market in self.researched_markets:
                market_counter += 1
                for item in PRODUCTS:
                    total_known_amount[item] += information[item][1]
        for item in PRODUCTS:
            avg_amount[item] = total_known_amount[item] / market_counter

        # start to find the best arbitrage opportunity
        for item in PRODUCTS:
            # nested loop to find any combination
            for market_1, information_1 in self.all_product_info.items():
                for market_2, information_2 in self.all_product_info.items():
                    # skip the same market
                    if market_1 == market_2:
                        continue
                    price_1 = information_1[item][0]
                    price_2 = information_2[item][0]
                    # if there is a good price different
                    if price_1 < price_2:
                        amount = information_1[item][1]
                        if amount is not None and amount == 0:
                            continue
                        if amount is None:
                            amount = avg_amount[item]
                        # based on assumption of history record to get the avaliable amount
                        # and calculate the profit
                        
                        #amount = min(amount, max_amount)
                        revenue = amount * (price_2 - price_1)
                        path_before_arbitrage = self.shortest_path(self.loc, market_1)
                        path_arbitrage = self.shortest_path(market_1, market_2)
                        
                        # based on the shortest path to measure the dark punishment
                        undirect_cost = 0
                        if type(path_before_arbitrage) == list:
                            for i in path_before_arbitrage:
                                if i in self.black_markets or i in self.grey_markets:
                                    undirect_cost += OUTSIDE_CIRCLE_PENALTY 
                        if type(path_arbitrage) == list:
                            for i in path_arbitrage:
                                if i in self.black_markets or i in self.grey_markets:
                                    undirect_cost += OUTSIDE_CIRCLE_PENALTY 
                        '''
                        if (path_arbitrage is not True) and \
                            (market_2 in self.black_markets or \
                                market_2 in self.grey_markets):
                            undirect_cost += OUTSIDE_CIRCLE_PENALTY * (len(path_arbitrage)/2)'''
                        revenue -= undirect_cost
                        
                        # debt punishment
                        max_amount = int((self.risk_attitude * self.gold)//price_1)
                        if amount > max_amount:
                            debt = self.gold - amount * price_1
                            total_debt = debt * ((1 + self.interest) ** len(path_arbitrage))
                            revenue -= total_debt

                        # star to rank the potenital action
                        self.current_best_aim.append(((-revenue), market_1, item, information_1[item][0] ,amount ,path_before_arbitrage))
        self.current_best_aim.sort()

    # code from kin
    def buy_item(self,item,item_amount,price):
        """
        Helper to buy an item, item_amount times
        """
        self.inventory_tracker[item] =  (self.inventory_tracker.get(item,(0,0))[0] + item_amount, price)
        self.gold -= item_amount * price
   
    # code from kin
    def sell_item(self,item,item_amount,price):
        """
        Helper to sell item based on item_amount
        """
        self.inventory_tracker[item] = (self.inventory_tracker[item][0] - item_amount,
                                        self.inventory_tracker[item][1])
        self.gold += price * item_amount



# code for testing
if __name__ == "__main__":

    #from Player import Player
    from kin import Player as P2
    def test():
        g = Game([Player(),Player(), Player(), Player(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2()], verbose=False)
        res = g.run_game()
        print(res[0])
        return res[0]
    
    g = Game([Player(),Player(),Player(), Player(),Player(),Player(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2()], verbose=False)
    #g2 = Game([Player(),Player(), Player(), Player(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2()], verbose=False)
    #g3 = Game([Player(),Player(), Player(), Player(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2()], verbose=False)
    #g4 = Game([Player(),Player(), Player(), Player(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2()], verbose=False)
    #g5 = Game([Player(),Player(), Player(), Player(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2(), P2()], verbose=False)
    res = g.run_game()
    #res2 = g2.run_game()
    #res3 = g3.run_game()
    #res4 = g4.run_game()
    #res5 = g5.run_game()
    print(res)
    #print(res2[0])
    #print(res3[0])
    #print(res4[0])
    #print(res5[0])
    
    #avg = (res[0] + res2[0] + res3[0] + res4[0])/5
    '''

    import os
    import random
    import time
    from multiprocessing import Pool, current_process 
    from time import ctime
    import numpy
    result = []
    p = Pool()
    for i in range(5):
        result.append(p.apply_async(test, args=())) 
    p.close()
    p.join() 
    result_list = [] 
    for res in result:
        result_list.append(res.get()) 
    final_result = []
    for res in result_list:
        final_result.append(res)
    print(numpy.mean(final_result))'''
