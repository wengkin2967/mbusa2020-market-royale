"""
    Basic player class to be subclassed.

    Andrew Turpin
    Sat 11 Apr 2020 18:02:37 AEST
"""
import Command
from Map import Map

class BasePlayer:
    """
        You SHOULD NOT ALTER THIS CLASS.
    """
    def __init__(self):
            # all three of these get set by game when it starts
        self.gold = None    # float
        self.goal = None    # dictionary {product:amount needed}
        self.map = None     # Map object

    def set_goal(self, goal): 
        """This function gets called by the game at the start to 
           set the goal attribute of the player object.
        """
        assert(type(goal) is dict)
        self.goal = goal

    def set_gold(self, gold): 
        """This function gets called by the game at the start to 
           set the gold attribute of the player object.
        """
        assert(type(gold) is float)
        self.gold = gold

    def set_map(self, map): 
        """This function gets called by the game at the start to 
           set the map attribute of the player object.
        """
        assert(isinstance(map, Map))
        self.map = map

    def take_turn(self, loc, this_market, info, black_markets, grey_markets):
        """@param loc Name of your current location on map as a str.
           @param this_market A dictionary {product:(price,amount)} of prices and amounts 
                              at this market (if you have researched, {} otherwise).
           @param info A dictionary {market:{product:price}} of information gleaned from other 
                       players that were here when you arrived.
           @param black_markets A list of market names (strings) that are Black.
           @param grey_markets A list of market names (strings) that are Grey.

           @return (cmd, data) cmd is one of Command.* and data is a tuple of necessary data for a command.
        """
        assert(type(loc) is str)
        assert(type(this_market) is dict)
        assert(type(info) is dict)

        return (Command.PASS, None)

        # return (Command.BUY, (this_market.keys()[0], this_market.values()[1]))  # example BUY
