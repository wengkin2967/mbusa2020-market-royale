import Command
from Map import Map
from BasePlayer import BasePlayer
import Market
import heapq as hq
import copy
from Priority_q_node import pq_node
from math import sqrt
from Market import PRODUCTS
from Game import OUTSIDE_CIRCLE_PENALTY, GOAL_BONUS

class Player(BasePlayer):
    def __init__(self, mode='MAX', max_depth=50, interest=0.1, max_buy=20):
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

        self.loc = None 
        self.this_market = None 
        self.info = None
        self.black_markets = None
        self.grey_markets = None
        
        self.same_loc = 0
        self.max_buy = max_buy

        self.next_best_move = None
        self.highest_score = None
        

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
        assert(type(loc) is str)
        assert(type(this_market) is dict)
        assert(type(info) is dict)
        self.loc = loc
        self.this_market = this_market 
        self.info = info
        self.black_markets = black_markets
        self.grey_markets = grey_markets
        # return (Command.BUY, (this_market.keys()[0], this_market.values()[1]))  # example BUY
    
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
                self.this_market = self.info[self.loc]
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
                price = self.info[self.loc][item]
                assert(data[0] in PRODUCTS)
                assert(type(data[1]) is int)
                if item not in self.inventory_tracker.keys():
                    return False
                if item_amount > self.inventory_tracker[item][0]:
                    return False
                
                new_amount = self.inventory_tracker[item][0] - item_amount
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
        while current_node.parent is not None:
            original_node = original_node.parent
        if self.next_best_move is None:
            self.next_best_move = original_node.action
            self.highest_score = current_node.acc_reward
        else:
            if self.highest_score < current_node.acc_reward:
                self.next_best_move = original_node.action
                self.highest_score = current_node.acc_reward
    
    def naive_dijkstra(self, loc, this_market, info, black_markets, grey_markets):
        priority_q = hq.heapify([])
        used_nodes = []
        potential = self.potential_action(first_action=True)
        for action in potential:
            simulation_player = copy.deepcopy(self)
            if simulation_player.simulation(action) is False:
                continue
            next_move_node = pq_node()
            next_move_node.first_node(action)
            next_move_node.set_value(simulation_player.get_reward(), simulation_player)
            hq.heappush(priority_q, next_move_node)
        while priority_q:
            current_node = hq.heappop(priority_q)
            if current_node.depth is not 1:
                current_player = current_node.status
                if current_player.simulation(current_node.action):
                    current_node.set_value(current_player.get_reward(), current_player)
                    self.propagate_back(current_node)
                    used_nodes.append(current_node)
            else:
                self.propagate_back(current_node)
                used_nodes.append(current_node)
            potential = current_node.potential_action(first_action=False)
            
            for action in potential:
                simulation_player = copy.deepcopy(current_node)
                next_move_node = pq_node()
                next_move_node.sub_node(current_node, action, simulation_player)
                hq.heappush(priority_q, next_move_node)










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

    def buy_item(self,item,item_amount,price):
        """
        Helper to buy an item, item_amount times
        """
        self.inventory_tracker[item] =  (self.inventory_tracker.get(item,(0,0))[0] + item_amount, price)
        self.gold -= item_amount * price
        return (Command.BUY,(item, item_amount))

    def potential_action(self, first_action):
        potential_list = []
        for neighbour in self.map.get_neighbours(self.loc):
            potential_list.append((Command.MOVE_TO, neighbour))

        if first_action:
            for item, data in self.this_market.items():
                amount = data[1]
                for i in range(1, amount + 1):
                    action = (Command.BUY, (item, i))
                    potential_list.append(action)
                if item in self.inventory_tracker.keys():
                    for i in range(1, self.inventory_tracker[item][0] + 1):
                        action = (Command.SELL, (item, i))
                        potential_list.append(action)
        else:
            items = self.info[self.loc]
            for item in items:
                for i in range(1, self.max_buy):
                    action = (Command.BUY, (item, i))
                    potential_list.append(action)
                if item in self.inventory_tracker.keys():
                    for i in range(1, self.inventory_tracker[item][0] + 1):
                        action = (Command.SELL, (item, i))
                        potential_list.append(action)
        return potential_list


        
if __name__ == "__main__":

    a = pq_node()
    a.first_node(Player(), 'action')
    b = pq_node()
    b.create_node(Player(), a,'action')
    print(a > b)
    print(a < b)
    print(a == b)
    c = []
    hq.heappush(c, a)
    hq.heappush(c, b)
    print(hq.heappop(c).depth)
    print(hq.heappop(c).depth)
    print(hq.heappop(c))
