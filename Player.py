import Command
import random
import pdb
from math import sqrt
from BasePlayer import BasePlayer
from Game import Game
from functools import reduce 
# Player class for the assignment

class Player(BasePlayer):
    """Player class for Market Royale. Developed By
        Syndicate 12."""
    
    def __init__(self):
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
    

    def take_turn(self, location, prices, info, bm, gm):
        # updates turns
        self.turn_tracker += 1

        # if(self.turn_tracker == 50 and self.gold < 2000):
        #     pdb.set_trace()

        # Adds information from any players inside the market
        for m in info.keys():
            self.player_info[m] = info[m]

        # List of location's neighbours
        neighbours = list(self.map.get_neighbours(location))

        # Define goals not achieved yet
        not_achieved_goals = self.goals_not_achieved()

        # Checks if market has been researched
        if(location not in self.researched_markets):
            self.researched_markets.append(location)
            return(Command.RESEARCH,None)
        # If market researched, should aim to buy for goals or sell
        else:
            # Add market info to tracker
            self.market_visited_info[location] = prices

            # Arrange goal based on cheapest to acquire
            priority_goals = sorted(not_achieved_goals, key= lambda x: prices.get(x,(999999,0))[0] * 
                                    abs(self.goal[x] - self.inventory_tracker.get(x,(0,0))[0]))
            
            # Selling if excess and can make a profit
            for item in self.goals_achieved():
                if (self.excess_item(item) and 
                    self.got_profit(prices.get(item,(0,0))[0],item)):

                    item_amount = self.inventory_tracker.get(item,(0,0))[0] - self.goal[item]
                    return self.sell_item(item,item_amount,prices.get(item,(0,0))[0])

            for item in priority_goals:
                
                # Sell if cannot meet goal
                if (self.turn_tracker >= 46 and 
                    self.inventory_tracker.get(item,(9999,9999))[0] < self.goal[item]):

                    item_amount = self.inventory_tracker[item][0]
                    return self.sell_item(item,item_amount,prices.get(item,(0,0))[0])

                # Checking if player info has valuable information
                if(item in prices.keys() and self.turn_tracker < 40):
                    for market in self.player_info.keys():
                        if (self.map.is_road(location,market) and 
                        self.player_info[market][item] < prices[item][0]
                        and self.worth_moving(item, prices[item], self.player_info[market][item],1000)):

                            return (Command.MOVE_TO, market)
                
                # For each item in price, check that there is enough
                # stock, enough gold, less than 10k and that goal
                # hasn't been met yet
                if(item in prices.keys() and prices[item][1] > 0 and 
                    self.goal_is_worth_and_enough_money(prices,item) and 
                    not self.goal_met(item)):

                    amount = min(self.goal[item], prices[item][1])
                    self.buy_item(item,amount,prices[item][0])
                    return (Command.BUY,(item, amount))
        
        # Moving if area is grey or black
        in_danger = self.move_if_danger(location,neighbours,bm,gm)
        if(in_danger):
            return in_danger


        node_distance = self.get_euclidean_distance_nodes()
        neighbours_distance = [(n,d) for (n,d) in node_distance.items() if n in neighbours]
        destination = min(neighbours_distance,key= lambda x: x[1])[0]
        # Go to closest market to the center if cant buy anything
        if(destination not in bm and destination not in gm):
            return (Command.MOVE_TO, destination)
        else:
            return (Command.PASS, None)

    # Moving Logic Functions

    def move_if_danger(self, location, neighbours, bm, gm):
        """
        Helper function for moving player if in danger of
        being in black or grey zones. Returns the command if player in danger.
        If not, return False.
        """
        # Dictionary of distances to center
        dist =  self.get_euclidean_distance_nodes()
        # Moving if area is grey or black
        if location in bm or location in gm:
            # Map neighbours to distance to center
            neighbours_distance = []
            for node in neighbours:
                neighbours_distance.append((node,dist[node]))
            
            neighbours_distance = sorted(neighbours_distance,key=lambda x: x[1])

            for (node,dist) in neighbours_distance:
                if node not in bm or node not in gm:
                    return (Command.MOVE_TO,node)

            # By Default, go to the one nearest to center
            return (Command.MOVE_TO, neighbours_distance[0])
        # When not in danger, return false
        return False
    
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

    # Buying logic functions

    def goal_is_worth_and_enough_money(self, prices, goal_item):
        """
        Helper function to check if the goal is worth to complete or not and
        whether the player has enough money to purchase the item. Also checks
        this condition for either completing the goal at once, or finishing
        the goal if there's partial inventory.
        """
        amount_spent =  self.goal[goal_item] * prices[goal_item][0]

        spending_limit = min(self.gold, 10000)

        return amount_spent < spending_limit
    
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

    def buy_item(self,item,item_amount,price):
        """
        Helper to buy an item, item_amount times
        """
        self.inventory_tracker[item] =  (self.inventory_tracker.get(item,(0,0))[0] + item_amount, price)
        self.gold -= item_amount * price
        return (Command.BUY,(item, item_amount))

    def worth_moving(self, item, item_price_amount, new_price, threshold):
        """
        Helper to  check if it is worth moving to the new market to purchase 
        product for achieving the goal by having a threshold difference
        """

        final_amount = min(self.goal[item], item_price_amount[1])
        difference_price = (item_price_amount[0] - new_price)

        return final_amount * difference_price  >= threshold

    #  Selling Logic Functions

    def goals_achieved(self):
        """
        Helper to return goals achieved.
        """

        return [goal for goal in self.goal.keys() if  self.goal_met(goal)]

    def sell_item(self,item,item_amount,price):
        """
        Helper to sell item based on item_amount
        """
        self.inventory_tracker[item] = (self.inventory_tracker[item][0] - item_amount,
                                        self.inventory_tracker[item][1])
        self.gold += price * item_amount
        return (Command.SELL, (item,item_amount))

    def excess_item(self,item):
        """
        Helper to see if inventory has excess of an item with respect to goal
        """
        return self.inventory_tracker.get(item,(0,0))[0] > self.goal[item]

    def got_profit(self,price,item):
        """
        Helper to determine whether selling item yields profit
        """
        price > self.inventory_tracker.get(item,(0,9999))[1]

