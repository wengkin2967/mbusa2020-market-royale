# Player class for assignment
from BasePlayer import BasePlayer
import Command
import pdb
import copy
from Game import OUTSIDE_CIRCLE_PENALTY
from Game import Game

UNKNOW = None
PATH_IN_TUPLE = -1
ITEM_IN_TUPLE = 1
AMOUNT_IN_TUPLE = -2
PRICE_IN_TUPLE = -3

class Player(BasePlayer):

    def __init__(self):
        super().__init__()

        self.player_info = {}
        self.research_markets = []
        self.inventory_tracker = {}
        self.turn_tracker = 0
        self.visited_markets = {}

        # new variable needed to store information
        self.black_market = None
        self.grey_market = None
        self.all_product_info = {}
        self.loc = None
    
    def take_turn(self, location, this_market, info, bm, gm):

        self.turn_tracker += 1
        
        # store necessary information
        self.loc = location 
        self.black_market = copy.deepcopy(bm)
        self.grey_market = copy.deepcopy(gm)
        for market, information in info.items():
            if market not in self.all_product_info:
                information = {product:(price, UNKNOW) for product, price in information.items()}
                self.all_product_info[market] = information
        if this_market:
            self.all_product_info[location] = copy.deepcopy(this_market)


        path = self.shortest_path(location, self.centrenode())
        if (len(path) > 1):
            path.pop(0)

        # Adds information from any players inside the market
        for m in info.keys():
            self.player_info[m] = info[m]


        priority_goals = sorted(self.goals_not_achieved(), key= lambda x: this_market.get(x,(999999,0))[0] * 
                                    abs(self.goal[x] - self.inventory_tracker.get(x,(0,0))[0]))
        
        # debug
        # if self.turn_tracker == 299:
        #     pdb.set_trace()
        #print(self.excess_item())


        # print information
        if False:
            print("PRIORITYGOALS",priority_goals)
            a = sorted(list(self.inventory_tracker.items()))
            inventory_list = [ (product, amount[0]) for product, amount in a]
            print("Inventory", inventory_list)
            print('Goal     ', sorted(list(self.goal.items())))
            print('---------------')
        
        # selling mode, check if there any excess items
        sell = self.selling_mode()
        if sell is not False:
            move = self.get_move_for_sell(sell)
            print('Selling mode', move)
            return(move)
        
        ''' Testing code forcing it to buy
        if True:
            if self.turn_tracker == 9:
                self.research_markets.append(location)
                return (Command.RESEARCH, None)
            if self.turn_tracker == 10:
                print('second turn')
                self.inventory_tracker['Hardware'] = (self.inventory_tracker['Hardware'][1]+5, this_market['Hardware'][0])
                self.gold -= 5 * this_market['Hardware'][0]
                return (Command.BUY, ('Hardware', 5))
        '''
        
        
        if (location in (bm + gm)):
            return (Command.MOVE_TO, path[0])
        elif location not in self.research_markets:
            self.research_markets.append(location)
            return (Command.RESEARCH, None)
        else:
            # Checking if next node on path has cheaper options for cheapest goal
            if (len(path) > 1 and path[0] in (self.player_info.keys()) and
                path[0] not in (bm + gm)):
                first_goal = priority_goals[0]
                if (this_market[first_goal][0] > self.player_info[path[0]]):
                    return (Command.MOVE_TO,path[0])

            for goal in priority_goals:
                amount = min(self.goal[goal], this_market.get(goal,(9999,9999))[1], self.goal[goal] - self.inventory_tracker.get(goal,(0,0))[0])
                if (this_market[goal][0] * amount  < min(10000, self.gold) ):
                    self.inventory_tracker[goal] = (self.inventory_tracker.get(goal,(0,0))[0] + amount, this_market[goal][0])
                    self.gold -= amount * this_market[goal][0]
                    return (Command.BUY, (goal,amount))
            
                # if (this_market[goal][0] * amount  < 10000 - (amount * self.goal[goal])):
                #     return (Command.BUY, (goal,amount))

        return (Command.MOVE_TO, path[0])    








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
            # suggest that we only add those not in gray or black market to the targetnodelist
            if node not in self.black_market and node not in self.grey_market:
                targetnodelist.append([node, x_abs + y_abs])
        return sorted (targetnodelist, key = lambda node: node[1])[0][0]

    def shortest_path(self, location, goal):
        """
        Finds shortest path between any location and centrenode using BFS
        """
        graph = self.map.map_data['node_graph']
        #keeps track of explored nodes
        explored = []
        #keeps track of all paths to be checked
        queue = [[location]]
        
        # return path if location is centrenode
        if location == goal:
            return [location]
        
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
                    if neighbour == goal:
                        return new_path
                explored.append(node)

    def goals_achieved(self):
        """
        Helper to return goals achieved.
        """

        return [goal for goal in self.goal.keys() if  self.goal_met(goal)]

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
    
    def excess_item(self):
        """
        Helper to return all excess items.
        """
        return [goal for goal in self.goal.keys() if self.excess_goal(goal)]

    def excess_goal(self, goal_item):
        """
        Helper to check whether a if this item is excess or not.
        """ 
        return self.inventory_tracker.get(goal_item,(0,0))[0] > \
                self.goal[goal_item]

    def selling_mode(self):
        """
        This code is trying to find the best offer price that we could sell
        our excess products
        """
        current_aim = []
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

                for i in path:
                    if i in self.black_market or i in self.grey_market:
                        undirect_cost += OUTSIDE_CIRCLE_PENALTY * 2

                # append for ranking to decide best action
                current_profit = revenue - undirect_cost
                total_len = 0
                if type(path) == list:
                    total_len += len(path)
                    revenue = revenue / total_len
                current_aim.append((-current_profit, market, item, information[item][0] ,excess ,path))
        # ranking for decdiding best action
        
        if len(current_aim) > 0:
            current_aim.sort()
            #pdb.set_trace()
            print(current_aim)
            # return format: tuple(target_selling_market_id, item_name, price, amount_need_to_sale, the path to that market)
            return current_aim[0][1:]
        else:
            # problem handling
            #print('no selling item')
            return False
    
    def get_move_for_sell(self, target_details):
        """
        based on our aim,
        and our current location
        to decide the action
        """
        
        if target_details is False:
            return (Command.PASS, None)
        if len(target_details[PATH_IN_TUPLE]) == 1:
            if self.loc not in self.research_markets:
                self.research_markets.append(self.loc)
                return (Command.RESEARCH, None)
            else:
                #pdb.set_trace()
                self.sell_item(target_details[ITEM_IN_TUPLE], target_details[AMOUNT_IN_TUPLE], target_details[PRICE_IN_TUPLE])
                #print((Command.SELL, (target_details[ITEM_IN_TUPLE], target_details[AMOUNT_IN_TUPLE])))
                return (Command.SELL, (target_details[ITEM_IN_TUPLE], target_details[AMOUNT_IN_TUPLE]))
    
        return Command.MOVE_TO, target_details[PATH_IN_TUPLE][1]

    # Kin's code
    def sell_item(self,item,item_amount,price):
        """
        Helper to sell item based on item_amount
        """
        #pdb.set_trace()
        self.inventory_tracker[item] = (self.inventory_tracker[item][0] - item_amount,
                                        self.inventory_tracker[item][1])
        self.gold += price * item_amount


if __name__ == "__main__":
    #from Player_2 import Player as p2
    g = Game([Player()], verbose=False)
    res = g.run_game()
    print(res)