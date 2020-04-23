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

        # if(self.turn_tracker == 50):
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
        # If market researched, should aim to buy for goals
        else:
            # Add market info to tracker
            self.market_visited_info[location] = prices

            # Arrange goal based on cheapest to acquire
            priority_goals = sorted(not_achieved_goals, key= lambda x: prices.get(x,(999999,0))[0] * abs(self.goal[x] - self.inventory_tracker.get(x,(0,0))[0]))
            
            for item in priority_goals:
                # Sell if cannot meet goal or if there is excess inventory
                if (self.turn_tracker >= 46 and self.inventory_tracker.get(item,(0,0))[0] < self.goal[item]):
                    return (Command.SELL, (item,self.inventory_tracker.get(item,(0,0))[0]))
                elif (self.inventory_tracker.get(item,(0,0))[0] > self.goal[item]):
                    return (Command.SELL, (item,self.inventory_tracker.get(item,(0,0))[0] - self.goal[item]))

                # Checking if player info has valuable information
                if(item in prices.keys() and self.turn_tracker < 40):
                    for market in self.player_info.keys():
                        if(self.map.is_road(location,market) and 
                        self.player_info[market][item] < prices[item][0]
                        and min(self.goal[item], prices[item][1]) * prices[item][0]  -  
                            min(self.goal[item],prices[item][1]) *  self.player_info[market][item] >= 1000):
                            return (Command.MOVE_TO, market)
                
                # For each item in price, check that there is enough
                # stock, enough gold, less than 10k and that goal
                # hasn't been met yet
                if(item in prices.keys() and prices[item][1] > 0 and self.goal_is_worth_and_enough_money(prices,item) and 
                    not self.goal_met(item)):
                    amount = min(self.goal[item], prices[item][1])
                    self.inventory_tracker[item] =  (self.inventory_tracker.get(item,(0,0))[0] + amount, prices[item][0])
                    self.gold -= amount * prices[item][0]
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