# Player class for assignment
from BasePlayer import BasePlayer
import Command
from Map import Map
from Game import Game


class Player(BasePlayer):
    """Minimal player."""
    
    def take_turn(self, location, prices, info, bm, gm):
        if location in bm or location in gm:
            return (Command.PASS, None)
        else:
            return (Command.MOVE_TO, self.checkconnection(location)[0])
    
    #returns list of black markets
    def bm(self):
        nodestatuslist = self.map.get_node_status()
        bmlist = []
        for statustuple in nodestatuslist:
            if statustuple[1] == 2:
                bmlist.append(statustuple[0])
        return bmlist
    
    #returns list of grey markets
    def gm(self):
        nodestatuslist = self.map.get_node_status()
        gmlist = []
        for statustuple in nodestatuslist:
            if statustuple[1] == 2:
                gmlist.append(statustuple[0])
        return gmlist

    #returns list of validnodes
    def checkconnection(self, location):
        validnodes = []
        for node in self.map.get_neighbours(location):
            if self.map.is_road(location, node):
                validnodes.append(node)
        return validnodes 