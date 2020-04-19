# Player class for the assignment
from BasePlayer import BasePlayer
from Game import Game
import Command
import random

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
        if location in (bm or gm):
            neighbours = list(self.map.get_neighbours(location))
            for i in neighbours:
                if i not in bm or gm:
                    return(Command.MOVE_TO,i)
            # Return a random neighbour if all are black or grey
            return(Command.MOVE_TO,neighbours[random.randint(0,len(neighbours)-1)])

        if(location not in self.researched_markets):
            self.researched_markets.append(location)
            return(Command.RESEARCH,None)
        elif(goals['Hardware'] * prices['Hardware'][0] < 10000 and inventory['Hardware'] < goals['Hardware']):
            amount = goals['Hardware'] - inventory['Hardware']
            inventory['Hardware'] += amount
            return (Command.BUY,('Hardware', amount))
        elif(goals['Food'] * prices['Food'][0] < 10000 and inventory['Food'] < goals['Food']):
            amount = goals['Food'] - inventory['Food']
            inventory['Food'] += amount
            return (Command.BUY,('Food', amount))
        elif(goals['Electronics'] * prices['Electronics'][0] < 10000 and inventory['Electronics'] < goals['Electronics']):
            amount = goals['Electronics'] - inventory['Electronics']
            inventory['Electronics'] += amount
            return (Command.BUY,('Electronics', amount))
        elif(goals['Social'] * prices['Social'][0] < 10000 and inventory['Social'] < goals['Social']):
            amount = goals['Social'] - inventory['Social']
            inventory['Social'] += amount
            return (Command.BUY,('Social', amount))
        
        return (Command.PASS, None)
    

