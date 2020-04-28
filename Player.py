import Command
from Map import Map
from BasePlayer import BasePlayer
import Market
import heapq as hq
import copy
from math import sqrt
from Market import PRODUCTS
from Game import OUTSIDE_CIRCLE_PENALTY, GOAL_BONUS, Game
import traceback
import time
import random
from collections import defaultdict
import pdb

UNKNOW = None
CHANGE_MODE_TIME = 0.6
CHANGE_MODE_TIME_2 = 0.85
RESEARCH_TIME = 0.025
STOP_ARBITRAGE = 0.94
STOP_TIME = 0.97


class Player(BasePlayer):
    """
    Player class for Market Royale by Syndicate 12

    Rough timeline of strategy in proportion of total turns: 
        0-60%: arbitrage stage
        60% - 85%: goal realisation stage
        85% ~: arbitrage stage

    The Strategy
    1)	0 - 2.5%: 
        Only research the markets without any trading.

    2)	2.5% - 60%: 
        Reset all goals to be 0 and collect information about prices and 
        quantities either from research or from other’s information. For 
        the markets without the quantity information, use the average quantity
        from other markets. First, calculate the total value of each product
        at each market by multiplying the price and quantity. Next, the 
        potential arbitrage revenue is the positive difference of total value 
        for each product between any 2 markets. The net arbitrage profit is 
        the difference between the arbitrage revenue and the total 
        black-market penalty incurred by moving between the 2 markets. 
        Then calculate the average arbitrage profit as dividing each net 
        arbitrage profit by the total number of steps needed to move 
        (from the current location to the first market and then the second 
        market in the arbitrage strategy – the first market is the one with 
        lower total value). Finally, exploit the arbitrage opportunity with 
        the highest average arbitrage profit by moving and trading at the 2 
        markets involved in the opportunity. The whole process above will be 
        repeated each turn.

    3)	60% - 85%: 
        Reset the goal to the initial requirement and fulfil the goal. Once 
        the goal is met, switch back to the arbitrage stage to keep making 
        arbitrage profit as described above. The longest possible time for 
        this goal realisation stage is from 60% ~85% of the total turns. That 
        means even if not all of the goals have been achieved by the 85%th 
        turn (255th in the 300-turn case), the player will stop achieving the 
        goal and instead restart to seek arbitrage opportunities. 
        
    4)	85% - 94%: 
        Arbitrage period – same strategy as in the 2.5% - 60% period.

    5)	94% - 97%: 
        Stop buying anymore, only sell the excess items at the highest possible
        average price.

    6)	97% - 100%: 
        Stop any trading and move along the shortest path to the safe zone 
        (or centre node); if already there, do nothing.


    """
    def __init__(self,
                 mode='MAX',
                 max_depth=50,
                 interest=0.1,
                 max_buy=10,
                 risk_attitude=0.95,
                 max_turn=300):
        super().__init__()

        # Records information about markets visited, includes price and amounts
        self.market_visited_info = {}

        # Tracker of info gained from other players (only product amount), will be regularly updated.
        self.player_info = {}

        # List of markets researched
        self.researched_markets = []

        # {product : (amount,price)}
        self.inventory_tracker = {}

        # Keep track of turn number
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
        self.list_of_all_action = []
        self.goal_met_or_not = False

    # Author : Jiaan Lin
    def take_turn(self, loc, this_market, info, black_markets, grey_markets):
        """@param loc: Name of your current location on map as a str.
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
        assert (type(loc) is str)
        assert (type(this_market) is dict)
        assert (type(info) is dict)
        self.current_loc = loc
        self.loc = loc
        self.this_market = this_market
        self.info = info
        self.black_markets = black_markets
        self.grey_markets = grey_markets
        self.next_best_move = (Command.RESEARCH, None)
        self.highest_score = None

        # Intrest rate consideration on Debt
        if self.gold < 0:
            i = -self.interest * self.gold
            self.gold -= i

        # track black market loss
        if self.loc in black_markets:
            self.gold -= 100

        # This part of code is used for the robot to arbitrage at first
        # by setting all goal to zero
        # Toggle True to False to disable it
        if True and self.first_time:
            self.first_time = False
            self.goal_copy = copy.deepcopy(self.goal)
            for item in self.goal.keys():
                self.goal[item] = 0

        # Go back to normal mode after a predetermined time
        # num of turn: 60% ~ 85%
        if self.turn_tracker > CHANGE_MODE_TIME * self.max_turn and len(
                self.excess_item()) == 0 and self.goal_met_or_not is False:
            self.goal = copy.deepcopy(self.goal_copy)
            if len(self.goals_not_achieved()) == 0:
                self.goal_met_or_not = True

        # Abandon those targets that cannot be met and keep arbitraging
        # num of turn: 85% ~ 100%
        elif self.turn_tracker > CHANGE_MODE_TIME_2 * self.max_turn:
            useless_items = self.goals_not_achieved()
            for i in useless_items:
                self.goal[i] = 0

        # num of turn: 0% ~ 60%
        else:
            # make sure to research as much as market as possible
            if self.loc not in self.researched_markets:
                self.researched_markets.append(self.loc)
                self.next_best_move = (Command.RESEARCH, None)
                return self.next_best_move

        # Updating information from current market and other markets (from competitors' data)
        for market, information in info.items():
            if market not in self.all_product_info:
                information = {
                    product: (price, UNKNOW)
                    for product, price in information.items()
                }
                self.all_product_info[market] = information
        if this_market:
            self.all_product_info[loc] = copy.deepcopy(this_market)

        # Make sure in the first 2.5 % round to be just researching markets.
        # Avoid if there is too less information causing potential wrong decision
        if True and self.turn_tracker < self.max_turn * RESEARCH_TIME:
            # Try to research as much as possible
            if self.loc not in self.researched_markets:
                self.researched_markets.append(self.loc)
                self.next_best_move = (Command.RESEARCH, None)
                return self.next_best_move
            # Avoid  going to the markets  already researched
            potential_node = [
                i for i in list(self.map.get_neighbours(loc))
                if i not in self.researched_markets
            ]
            if potential_node:
                self.next_best_move = (Command.MOVE_TO,
                                       random.choice(potential_node))
                return self.next_best_move

        # Main method, used to execute decided the action;
        # this method will modify self.next_best_action for return
        try:
            self.mode_decision()
        except Exception as e:
            # If something goes wrong, move randomely
            traceback.print_exc()
            print(f'Exception Error: {e}')
            potential_node = [i for i in list(self.map.get_neighbours(loc))]
            self.next_best_move = (Command.MOVE_TO,
                                   random.choice(potential_node))
        # This print function below is used for debugging
        # print(self.next_best_move)
        self.list_of_all_action.append([
            self.turn_tracker, self.next_best_move, self.goal,
            self.inventory_tracker, self.gold
        ])

        # Returns what we want to do
        return self.next_best_move

    # Author: Kin Lee
    def goals_not_achieved(self):
        """
        Helper to return all goals not yet achieved.
        """
        return [goal for goal in self.goal.keys() if not self.goal_met(goal)]

    # Author: Kin Lee
    def goal_met(self, goal_item):
        """
        Helper to check whether a goal item has been achieved.
        """
        return self.inventory_tracker.get(goal_item,(0,0))[0] >= \
                    self.goal[goal_item]

    # Author: Weng Kin Lee
    def excess_item(self):
        """
        Helper to return all goals not yet achieved.
        """
        return [goal for goal in self.goal.keys() if self.excess_or_not(goal)]

    # Author: Weng Kin Lee
    def excess_or_not(self, goal_item):
        """
        Helper to check whether a goal item has been achieved.
        """
        return self.inventory_tracker.get(goal_item,(0,0))[0] > \
                    self.goal[goal_item]
    # Author : Jiaan Lin              
    def mode_decision(self):
        """
        This method is based on the current situation to
        1. buy for meeting the goal
        2. arbitrage buying
        3. arbitrage selling
        eventually it will modify self.next_best_move for return to game
        """
        # Resets the ranking list
        self.current_best_aim = []

        # If we do not meet the goal, try to buy something to meet the goal
        if len(self.goals_not_achieved()) > 0 and self.turn_tracker <= int(
                self.max_turn * STOP_TIME):
            self.search_best_aim()
            self.get_move()
            return

        # If we already meet the goal or goal is 0 (first 60% turns),
        # we start to arbitrage
        # buy low
        if (len(self.excess_item()) == 0 or (len(self.goals_not_achieved()) > 0 and self.current_best_aim[0][0]>0))\
             and self.turn_tracker <= int(self.max_turn * STOP_ARBITRAGE):
            if self.turn_tracker < CHANGE_MODE_TIME * self.max_turn or self.goal_met_or_not:
                # find aim for arbitrage
                self.search_best_arbitrage()
                try:
                    # if there have profit in the best aim
                    if (self.current_best_aim[0][0] < 0):
                        self.get_move()
                        return
                except:
                    pass

        # If we have bought something from the arbitrage buying process
        # we will sell those things at a higest price as soon as possible
        if len(self.excess_item()) > 0 and self.turn_tracker <= int(
                self.max_turn * STOP_TIME):
            self.selling_mode()
            self.get_move(mode='SELL')
            return

        # If we have no purpose (goal met and no arbitrage and at the end 5% of turns)
        # try to walk to the middle avoid balck/gray areas
        centre = self.centrenode()
        path = self.shortest_path(self.loc, centre)
        # The print function below is used to track the path for debugging
        #print(f'escape: from {self.loc} to {path}')
        if path is not True:
            self.next_best_move = (Command.MOVE_TO, path[1])
        else:
            self.next_best_move = (Command.PASS, None)

    # Author : Bingxin Lin
    def centrenode(self):
        """
        Finds centrenode based mapwidth and mapheight
        """
        targetnodelist = []
        mapheight = (self.map.map_height) / 2
        mapwidth = (self.map.map_width) / 2
        for node, coordinates in self.map.map_data['node_positions'].items():
            x, y, circlestatus = coordinates
            x_abs = abs(mapwidth - x)
            y_abs = abs(mapheight - y)
            if node not in self.black_markets or node not in self.grey_markets:
                targetnodelist.append([node, x_abs + y_abs])
        return sorted(targetnodelist, key=lambda node: node[1])[0][0]

    # Author : Beryl Zhang
    def selling_mode(self):
        """
        This code is trying to find the best offer price that we could sell
        our excess products
        """

        # check every item
        for item in self.excess_item():
            # check if there is any excess item
            excess = self.inventory_tracker.get(item,
                                                (0, 0))[0] - self.goal[item]

            # if there is no excess, do nothing
            if excess <= 0:
                continue
            # start to find the best market
            for market, information in self.all_product_info.items():
                # based on price to check the selling profits
                price = information[item][0]
                revenue = price * excess
                indirect_cost = 0
                path = self.shortest_path(self.loc, market)
                # add balck market arbitrage buying to reduce revenue
                if type(path) == list:
                    for i in path:
                        if i in self.black_markets or i in self.grey_markets:
                            indirect_cost += OUTSIDE_CIRCLE_PENALTY

                # append for ranking to decide best action
                current_profit = revenue - indirect_cost
                total_len = 0
                if type(path) == list:
                    total_len += len(path)
                    revenue = revenue / total_len
                self.current_best_aim.append(
                    (-current_profit, market, item, information[item][0],
                     excess, path))
        # ranking for decdiding best action
        self.current_best_aim.sort()
    
    # Author : Weng Kin Lee
    def get_move(self, mode='BUY'):
        """
        Based on the ranking of our aim,
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
            # if we already research the current best offer market , then apply the action
            if self.loc in self.researched_markets:
                # buying
                if mode == 'BUY':
                    self.next_best_move = (Command.BUY,
                                           (self.current_best_aim[0][2],
                                            self.current_best_aim[0][4]))
                    self.buy_item(self.current_best_aim[0][2],
                                  self.current_best_aim[0][4],
                                  self.current_best_aim[0][3])
                    return
                # selling
                if mode == 'SELL':
                    self.next_best_move = (Command.SELL,
                                           (self.current_best_aim[0][2],
                                            self.current_best_aim[0][4]))
                    self.sell_item(self.current_best_aim[0][2],
                                   self.current_best_aim[0][4],
                                   self.current_best_aim[0][3])
                    return
            # if we do not research the market yet, research
            else:
                self.next_best_move = (Command.RESEARCH, None)
                self.researched_markets.append(self.loc)
                return
        # if we not reach our aim yet, we keep moving
        else:
            self.next_best_move = (Command.MOVE_TO,
                                   self.current_best_aim[0][-1][1])
    # Author: Esther Liu
    def search_best_aim(self):
        """
        This method is aiming to find the best price for us to meet our goal
        """
        # iterate every market to find the best price
        for goal_item in self.goals_not_achieved():
            for market, information in self.all_product_info.items():
                # find out what goal is still lacking 
                lacking = self.goal[goal_item] - self.inventory_tracker.get(
                    goal_item, (0, 0))[0]
                revenue = GOAL_BONUS
                # if there is no item avaliable, give up this market
                if information[goal_item][1] == 0:
                    continue
                # if we do not research the market yet, we just make an
                # assumption that there is enough item for buying
                if information[goal_item][1] is None:
                    pass
                # if there is low amount, we just buy the available amount
                elif information[goal_item][1] < lacking:
                    revenue = GOAL_BONUS / lacking
                    lacking = information[goal_item][1]
                    revenue = revenue * lacking
                # calculate the purchasing cost
                direct_cost = (information[goal_item][0] * lacking)
                indirect_cost = 0

                # account for the punishment from black market
                path = self.shortest_path(self.loc, market)

                if type(path) == list:
                    for i in path:
                        if i in self.black_markets or i in self.grey_markets:
                            indirect_cost += OUTSIDE_CIRCLE_PENALTY

                # risk controlling
                if direct_cost + indirect_cost > self.risk_attitude * self.gold:
                    continue

                # based on the net profit to rank those aims
                current_profit = revenue - direct_cost - indirect_cost
                total_len = 0
                if type(path) == list:
                    total_len += len(path)
                    revenue = revenue / total_len
                self.current_best_aim.append(
                    (-current_profit, market, goal_item,
                     information[goal_item][0], lacking, path))
        # rank those avaliable option
        self.current_best_aim.sort()

    # Author : Binxing Lin
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
                    new_path = list(path)
                    new_path.append(neighbour)
                    queue.append(new_path)
                    #return path if neighbour is centrenode
                    if neighbour == location_2:
                        return new_path
                explored.append(node)
    
    # Author : Shira Aretti
    def search_best_arbitrage(self):
        """
        This method is aming to find the best offer price and selling price
        in the map, so that we can arbitrage and make profit
        """
        # Make an assumption about the avaliable amount of item in those
        # market which is not researched yet
        # Assumption: those market have the average amount avaliable
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

        # Start to find the best arbitrage opportunity
        for item in PRODUCTS:
            # nested loop to find any combination
            for market_1, information_1 in self.all_product_info.items():
                for market_2, information_2 in self.all_product_info.items():
                    # skip the same market
                    if market_1 == market_2:
                        continue
                    price_1 = information_1[item][0]
                    price_2 = information_2[item][0]
                    # if there is a good price difference
                    if price_1 < price_2:
                        amount = information_1[item][1]
                        if amount is not None and amount == 0:
                            continue
                        if amount is None:
                            amount = avg_amount[item]
                        amount = min([self.gold // price_1, amount])
                        # Based on assumption of history record to get the avaliable amount
                        # and calculate the profit

                        #amount = min(amount, max_amount)
                        revenue = amount * (price_2 - price_1)
                        path_before_arbitrage = self.shortest_path(
                            self.loc, market_1)
                        path_arbitrage = self.shortest_path(market_1, market_2)

                        # based on the shortest path to measure the black market penalties
                        indirect_cost = 0
                        if type(path_before_arbitrage) == list:
                            for i in path_before_arbitrage:
                                if i in self.black_markets or i in self.grey_markets:
                                    indirect_cost += OUTSIDE_CIRCLE_PENALTY
                        if type(path_arbitrage) == list:
                            for i in path_arbitrage:
                                if i in self.black_markets or i in self.grey_markets:
                                    indirect_cost += OUTSIDE_CIRCLE_PENALTY

                        revenue -= indirect_cost

                        # Debt penalties
                        if self.gold < (amount * price_1 + indirect_cost):
                            debt = amount * price_1 - self.gold + indirect_cost
                            total_debt = debt * ((1 + self.interest +
                                                  (1 - self.risk_attitude))**
                                                 len(path_arbitrage))
                            # risk averse
                            # total_debt = total_debt * (1 + (1 - self.risk_attitude))
                            revenue -= total_debt
                        total_len = 0
                        # Calculate the average return for each step
                        if type(path_before_arbitrage) == list:
                            total_len += len(path_before_arbitrage)
                        if type(path_arbitrage) == list:
                            total_len += len(path_arbitrage)
                        if total_len > 0:
                            revenue = revenue / total_len
                        # Start to rank the potenital action
                        self.current_best_aim.append(
                            ((-revenue), market_1, item,
                             information_1[item][0], amount,
                             path_before_arbitrage))
        self.current_best_aim.sort()

    # Author: Weng Kin Lee
    def buy_item(self, item, item_amount, price):
        """
        Helper to buy an item, item_amount times
        """
        self.inventory_tracker[item] = (
            self.inventory_tracker.get(item, (0, 0))[0] + item_amount, price)
        self.gold -= item_amount * price

     # Author: Weng Kin Lee
    def sell_item(self, item, item_amount, price):
        """
        Helper to sell item based on item_amount
        """
        self.inventory_tracker[item] = (self.inventory_tracker[item][0] -
                                        item_amount,
                                        self.inventory_tracker[item][1])
        self.gold += price * item_amount