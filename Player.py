import Command
import random
import pdb
from math import sqrt
from BasePlayer import BasePlayer
from Game import Game
# Player class for the assignment

class Player(BasePlayer):
    """Player class for Market Royale. Developed By
        Syndicate 12."""
    
    def __init__(self):
        super().__init__()
        self.market_visited_info = {}
        self.player_info = {}
        self.researched_markets = []
        # {product : (amount,price)}
        self.inventory_tracker = {}
        self.turn_tracker = 0
    

    def take_turn(self, location, prices, info, bm, gm):
        # pdb.set_trace()
        # updates turns
        self.turn_tracker += 1

        # Adds information from any players inside the market
        for m in info.keys():
            self.player_info[m] = info[m]

        neighbours = list(self.map.get_neighbours(location))

        # Moving if area is grey or black
        in_danger = self.move_if_danger(location,neighbours,bm,gm)
        if(in_danger):
            return in_danger

        # Checks if market has been researched
        if(location not in self.researched_markets):
            self.researched_markets.append(location)
            return(Command.RESEARCH,None)
        # If market researched, should aim to buy for goals
        else:
            # Add market info to tracker
            self.market_visited_info[location] = prices
            # For each item in price, check that there is enough
            # stock, enough gold, less than 10k and that goal
            # hasn't been met yet
            for item in prices.keys():
                if(prices[item][1] >= self.goal[item] and 
                self.goal[item] * prices[item][0] < self.gold and 
                self.goal[item] * prices[item][0] < 10000 and 
                self.inventory_tracker.get(item,(0,0))[0] < self.goal[item]):
                    amount = self.goal[item] 
                    self.inventory_tracker[item] =  (self.inventory_tracker.get(item,0) + amount, prices[item][0])
                    self.gold -= amount * prices[item][0]
                    return (Command.BUY,(item, amount))


        # Go to random location that is not black or grey, if either
        # stay in the same market
        destination = neighbours[random.randint(0,len(neighbours)-1)]
        if(destination not in bm and destination not in gm):
            return (Command.MOVE_TO, destination)
        else:
            return (Command.PASS, None)

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