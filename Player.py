# Player class for assignment

from BasePlayer import BasePlayer
import Command
from Map import Map
from Game import Game
import random
from math import sqrt
from collections import defaultdict

class Player(BasePlayer):
    """Minimal player."""
    
   # def __init__(self):
    #    super().__init__()
    
    
    def take_turn(self, location, prices, info, bm, gm):
        if self.danger(location,bm,gm) or location in bm or location in gm:
            return (Command.MOVE_TO, self.move(location))
        else:
            return (Command.PASS, None)
    
    #returns true if only 1 connecting node is white
    def danger(self, location, bm, gm):
        counter = 0
        for node in list(self.map.get_neighbours(location)):
            #white markets
            if node not in bm or node not in gm:
                counter += 1
        if counter < 2:
            return True
        else:
            return False

    #returns node that leads to target node
    def move(self, location):
        availablenodes = list(self.map.get_neighbours(location))
        d = defaultdict(int)
        for node in availablenodes:
            d[node] = self.dist(node)
        d = sorted(d.items(), key = lambda k: k[1])
        return d[0][0]
        
    #finds target_node based on map height and map width
    def centrenode(self):
       x = []
       y = []
       node = []
       targetmapheight = (self.map.map_height)/2
       targetmapwidth = (self.map.map_width)/2
       for i in self.map.map_data['node_positions']:
           node.append(i)
           x.append(self.map.map_data['node_positions'][i][0])
           y.append(self.map.map_data['node_positions'][i][1])
       coordinates = zip(node,x,y)
       targetnodelist = []
       for node,x,y in coordinates:
           x_abs = abs(targetmapwidth - x)
           y_abs = abs(targetmapheight - y)
           targetnodelist.append([node, x_abs+y_abs])
       return sorted(targetnodelist, key = lambda node: node[1])[0][0]
   
    #function to calculate distance between target node and current loc
    def dist(self, location):
       x_target = self.map.map_data['node_positions'][self.centrenode()][0]
       y_target = self.map.map_data['node_positions'][self.centrenode()][1]
       x_loc = self.map.map_data['node_positions'][location][0]
       y_loc = self.map.map_data['node_positions'][location][1]
       dist = sqrt(((x_target-x_loc)**2)+((y_target-y_loc)**2))
       return dist