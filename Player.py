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

class Player(BasePlayer):
    def __init__(self, mode='MAX', max_depth=50, interest=0.1, max_buy=10):
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

        self.mode = mode
        self.max_depth = max_depth
        self.interest = interest

        self.current_loc = None
        self.loc = None 
        self.this_market = None 
        self.info = None
        self.black_markets = None
        self.grey_markets = None
        
        self.same_loc = 0
        self.max_buy = max_buy

        self.next_best_move = None
        self.highest_score = None
        self.generated_nodes = 0
        self.start_time = None
        self.depth = None
        self.devide = 5

    def simulate_map(self, node, action):
        pass

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
        self.depth = 0
        self.next_best_move = None
        self.highest_score = None
        # return (Command.BUY, (this_market.keys()[0], this_market.values()[1]))  # example BUY
        print(self.goal)
        return_action = self.naive_dijkstra()
        if return_action[0] == Command.RESEARCH:
            self.researched_markets.append(loc)

        if not self.researched_markets:
            self.researched_markets.append(loc)
            return (Command.RESEARCH, 0)
        #print(self.depth)
        print(return_action)
        if return_action[0] is Command.BUY:
            self.buy_item(return_action[1][0], return_action[1][1], this_market[return_action[1][0]][0])
        if return_action[0] is Command.SELL:
            self.sell_item(return_action[1][0], return_action[1][1], this_market[return_action[1][0]][0])
        print(self.inventory_tracker)
        return return_action
    
    def simulation(self, action):
        
        if self.gold < 0:
            i = - self.interest * self.gold
            self.gold -= i

        if self.map.outside_circle(self.loc):
            self.gold -= OUTSIDE_CIRCLE_PENALTY
        
        cmd, data = action
        if cmd == Command.MOVE_TO:
            assert(type(data) is str)
            if self.map.is_road(self.loc, data):
                self.loc = data
            else:
                return False
        elif cmd == Command.BUY:
            if self.loc not in self.researched_markets:
                return False
            else:
                if self.gold < 0:
                    return False
                else:
                    assert(len(data) == 2)
                    data = list(data)
                    item, item_amount = data
                    if self.loc == self.current_loc:
                        price = self.this_market[item][0]
                    else:
                        price = self.info[self.loc][item]

                    if item not in self.inventory_tracker.keys():
                        self.inventory_tracker[item] =  (item_amount, price)
                    else:
                        new_amount = self.inventory_tracker[item][0] + item_amount
                        new_price = (self.inventory_tracker[item][0] * self.inventory_tracker[item][1] + price * item_amount)/new_amount
                        self.inventory_tracker[item] =  (new_amount, new_price)
                    self.gold -= item_amount * price

        elif cmd == Command.SELL:
            if self.loc not in self.researched_markets:
                return False
            else:
                assert(len(data) == 2)
                data = list(data)
                item, item_amount = data
                if self.loc == self.current_loc:
                    price = self.this_market[item][0]
                else:
                    price = self.info[self.loc][item]
                #price = self.info[self.loc][item]
                assert(data[0] in PRODUCTS)
                assert(type(data[1]) is int)
                if item not in self.inventory_tracker.keys():
                    return False
                if item_amount > self.inventory_tracker[item][0]:
                    return False
                
                new_amount = self.inventory_tracker[item][0] - item_amount
                if new_amount == 0:
                    new_price = 0
                else:
                    new_price = (self.inventory_tracker[item][0] * self.inventory_tracker[item][1] - price * item_amount)/new_amount
                self.inventory_tracker[item] =  (new_amount, new_price)
                self.gold += item_amount * price


        elif cmd == Command.RESEARCH:
            self.researched_markets.append(self.loc)
        
        return True

    def get_reward(self):
        score = 0
        met_goals = self.goals_achieved()
        score = GOAL_BONUS * len(met_goals) + self.gold
        return score

    def propagate_back(self, current_node):
        original_node = current_node
        while original_node.parent is not None:
            original_node = original_node.parent
        if self.next_best_move is None:
            self.next_best_move = original_node.action
            self.highest_score = current_node.acc_reward
        else:
            if self.highest_score < current_node.acc_reward:
                self.next_best_move = original_node.action
                self.highest_score = current_node.acc_reward
                print('*****************')
                print(self.next_best_move)
                print(self.highest_score)
                print('*****************')
    
    def naive_dijkstra(self):
        priority_q = []
        used_nodes = []
        potential = self.potential_action(first_action=True)
        for action in potential:
            #print(action)
            simulation_player = copy.deepcopy(self)
            if simulation_player.simulation(action) is False:
                continue
            next_move_node = pq_node()
            next_move_node.first_node(action)
            next_move_node.set_value(simulation_player.get_reward(), simulation_player)
            hq.heappush(priority_q, next_move_node)
        
        while priority_q:
            if self.turn_tracker > 1:
                #print('2')
                pass
            current_node = hq.heappop(priority_q)
            used_nodes.append(current_node)
            potential = current_node.status.potential_action(first_action=False)
            #print(potential)
            for action in potential:
                #if time.perf_counter() - self.start_time >= 10:
                if self.depth is not None and self.depth >= 4:
                    return self.next_best_move
                if self.turn_tracker > 1:

                    #print(action)
                    #print(current_node.status.inventory_tracker)
                    pass
                simulation_player = copy.deepcopy(current_node.status)
                self.generated_nodes += 1
                if simulation_player.simulation(action):
                    next_move_node = pq_node()
                    next_move_node.sub_node(current_node, action)
                    next_move_node.set_value(simulation_player.get_reward(), simulation_player)
                    self.depth = next_move_node.depth
                    self.propagate_back(next_move_node)
                    hq.heappush(priority_q, next_move_node)
                    if self.turn_tracker > 1:
                        pass
                        #print(action)
                        #print(simulation_player.get_reward())
                        #print('---------------------')
        return self.next_best_move
                










    def get_euclidean_distance_nodes(self):
        """
        Helper function to get the euclidean distance of each node from the center of map.
        Returns a list of distances
        """
        pos = self.map.map_data['node_positions']
        map_width = self.map.map_width
        map_height = self.map.map_height
        dist = {}

        # Populate the dist dictionary
        for node in pos.keys():
            dist[node] = sqrt((map_width/2.0 - pos[node][0])**2 + (map_height/2.0 - pos[node][1])**2)
            # dist[node] = abs(map_width/2.0 - pos[node][0]) + abs(map_height/2.0 - pos[node][1])

        return dist

    def goal_met(self, goal_item):
        """
        Helper to check whether a goal item has been achieved.
        """
        return self.inventory_tracker.get(goal_item,(0,0))[0] >= \
                    self.goal[goal_item]

    def goals_not_achieved(self):
        """
        Helper to return all goals not yet achieved.
        """
        return [goal for goal in self.goal.keys() if not self.goal_met(goal)]
    
    def goals_achieved(self):
        """
        Helper to return goals achieved.
        """

        return [goal for goal in self.goal.keys() if  self.goal_met(goal)]

    def buy_item(self, item, item_amount, price):
        """
        Helper to buy an item, item_amount times
        """
        self.inventory_tracker[item] =  (self.inventory_tracker.get(item,(0,0))[0] + item_amount, price)
        self.gold -= item_amount * price

    def sell_item(self, item, item_amount, price):
        """
        Helper to sell item based on item_amount
        """
        self.inventory_tracker[item] = (self.inventory_tracker[item][0] - item_amount,
                                        self.inventory_tracker[item][1])
        self.gold += price * item_amount

    def potential_action(self, first_action):
        if self.turn_tracker > 1:
            pass

        potential_list = []
        if self.loc not in self.researched_markets:
            potential_list.append((Command.RESEARCH, None))

        for neighbour in self.map.get_neighbours(self.loc):
            potential_list.append((Command.MOVE_TO, neighbour))
        #print(f'current{first_action}')
        #try:
        if first_action:
            for item, data in self.this_market.items():
                if item in self.inventory_tracker.keys():
                    amount = self.goal[item] - self.inventory_tracker[item][0]
                else:
                    amount = self.goal[item]
                if amount > 0:
                    action = (Command.SELL, (item, amount))
                    potential_list.append(action)
                '''
                amount = data[1]
                range_step = (amount + 1)//self.devide
                if range_step == 0:
                    range_step = 1
                for i in range(1, amount + 1, range_step):
                    action = (Command.BUY, (item, i))
                    potential_list.append(action)'''
                if item in self.inventory_tracker.keys():
                    amount = self.inventory_tracker[item][0] - self.goal[item]
                    if amount > 0:
                        action = (Command.SELL, (item, amount))
                        potential_list.append(action)
        else:

            if self.loc == self.current_loc:
                items = self.this_market.keys()
            else:
                items = []
                if self.loc in self.info.keys():
                    items = self.info[self.loc].keys()
            #print(items)
            #print('--------')
            #if self.loc not in self.info.keys():
            #    items = self.this_market
            #else:
            #    items = self.info[self.loc]
            for item in items:
                '''range_step = (self.max_buy//self.devide) // self.devide
                if range_step == 0:
                    range_step = 1
                for i in range(1, self.max_buy, range_step):
                    action = (Command.BUY, (item, i))
                    potential_list.append(action)'''
                if item in self.inventory_tracker.keys():
                    amount = self.goal[item] - self.inventory_tracker[item][0]
                else:
                    amount = self.goal[item]
                if amount > 0:
                    action = (Command.SELL, (item, amount))
                    potential_list.append(action)

                if item in self.inventory_tracker.keys():
                    amount = self.inventory_tracker[item][0] - self.goal[item]
                    if amount > 0:
                        action = (Command.SELL, (item, amount))
                        potential_list.append(action)
                #print(potential_list)
        #except:
        #    print('some error')
        #print(potential_list)
        return potential_list


        
if __name__ == "__main__":

    from Player import Player
    from kin import Player as P2
    g = Game([Player(),P2(), P2()], verbose=True)
    res = g.run_game()
    print(res)
