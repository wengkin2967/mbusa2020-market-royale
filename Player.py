# Player class for assignment
from BasePlayer import BasePlayer
import Command

 

class Player(BasePlayer):

    def __init__(self):
        pass
    
    def take_turn(self, loc, this_market, info, black_markets, grey_markets):
        return (Command.RESEARCH, None)