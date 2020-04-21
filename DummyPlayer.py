# Player class for the assignment
from BasePlayer import BasePlayer
from Game import Game
import Command
import random

class DummyPlayer(BasePlayer):
    """Minimal player."""

    def take_turn(self, location, prices, info, bm, gm):
        neighbours = list(self.map.get_neighbours(location))
        # Moving if area is grey or black
        if location in bm or location in gm:
            for i in neighbours:
                if i not in bm and i not in gm:
                    return(Command.MOVE_TO,i)
            # Return a random neighbour if all are black or grey
            return(Command.MOVE_TO,neighbours[random.randint(0,len(neighbours)-1)])
        return (Command.PASS, None)

