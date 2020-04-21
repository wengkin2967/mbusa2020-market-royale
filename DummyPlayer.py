# Player class for the assignment
from BasePlayer import BasePlayer
from Game import Game
import Command
import random

class DummyPlayer(BasePlayer):
    """Minimal player."""

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
        neighbours = list(self.map.get_neighbours(location))
        # Moving if area is grey or black
        if location in bm or location in gm:
            for i in neighbours:
                if i not in bm and i not in gm:
                    return(Command.MOVE_TO,i)
            # Return a random neighbour if all are black or grey
            return(Command.MOVE_TO,neighbours[random.randint(0,len(neighbours)-1)])

        if(location not in self.researched_markets):
                self.researched_markets.append(location)
                return(Command.RESEARCH,None)
        else:
            for item in prices.keys():
                if(self.goal[item] * prices[item][0] < 10000 and self.inventory_tracker.get(item,0) < self.goal[item]):
                    amount = self.goal[item] - self.inventory_tracker.get(item,0)
                    self.inventory_tracker[item] = self.inventory_tracker.get(item,0) + amount
                    self.gold -= self.goal[item] * prices[item][0]
                    return (Command.BUY,(item, amount))            

        return (Command.PASS, None)