# Player class for the assignment
from BasePlayer import BasePlayer
from Game import Game
import Command

class Player(BasePlayer):
    """Minimal player."""
    
    def __init__(self):
        super().__init__()
        self.info_tracker = {}
        self.inventory_price_tracker = {}
    

    def take_turn(self, location, prices, info, bm, gm):
        print(self,location)
        if location in (bm or gm):
            for i in self.map.get_neighbours(location):
                if i not in bm or gm:
                    return(Command.MOVE_TO,i)
        return (Command.PASS, None)

