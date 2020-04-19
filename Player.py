import Command
import random
from BasePlayer import BasePlayer
from Game import Game
# Player class for the assignment

class Player(BasePlayer):
    """Minimal player."""
    
    def __init__(self):
        super().__init__()
        self.info_tracker = {}
        self.inventory_price_tracker = {}
        self.researched_markets = []
        self.inventory = {
            'Food': 0,
            'Electronics': 0,
            'Social': 0,
            'Hardware':0
        }
    

    def take_turn(self, location, prices, info, bm, gm):
        goals = self.goal
        inventory = self.inventory
        # Moving if area is grey or black
        if location in bm or location in gm:
            neighbours = list(self.map.get_neighbours(location))
            for i in neighbours:
                if i not in bm and i not in gm:
                    return(Command.MOVE_TO,i)
            # Return a random neighbour if all are black or grey
            return(Command.MOVE_TO,neighbours[random.randint(0,len(neighbours)-1)])

        if(location not in self.researched_markets):
            self.researched_markets.append(location)
            return(Command.RESEARCH,None)
        else:
            for item in goals.keys():
                if(goals[item] * prices[item][0] < 10000 and inventory[item] < goals[item]):
                    amount = goals[item] - inventory[item]
                    inventory[item] += amount
                    self.gold -= goals[item] * prices[item][0]
                    return (Command.BUY,(item, amount))
        return (Command.PASS, None)