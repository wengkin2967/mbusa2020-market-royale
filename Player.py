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
    
    def danger(self, location, bm, gm):
        """
        Function that returns true or false if in danger
        """
        counter = 0
        for node in list(self.map.get_neighbours(location)):
            #white markets
            if node not in bm or node not in gm:
                counter += 1
        if counter < 2:
            return True
        else:
            return False

    def centrenode(self): 
        """
        Finds centrenode based mapwidth and mapheight
        """
        targetnodelist = []
        mapheight = (self.map.map_height)/2
        mapwidth = (self.map.map_width)/2
        for node, coordinates in self.map.map_data['node_positions'].items():
            x, y, circlestatus = coordinates
            x_abs = abs(mapwidth - x)
            y_abs = abs(mapheight - y)
            targetnodelist.append([node, x_abs + y_abs])
        return sorted (targetnodelist, key = lambda node: node[1])[0][0]

    def shortest_path(self, location, goal):
        """
        Finds shortest path between any location and centrenode using BFS
        """
        graph = self.map.map_data['node_graph']
        #keeps track of explored nodes
        explored = []
        #keeps track of all paths to be checked
        queue = [[location]]
        
        # return path if location is centrenode
        if location == goal:
            return location
        
        # loops until all possible paths are checked
        while queue:
            #pop first path from queue
            path = queue.pop(0)
            #gets last node from the path
            node = path[-1]
            if node not in explored:
                neighbours = graph[node]
                #go through all neighbournodes, construct new path
                #and push to queue
                for neighbour in neighbours:
                    new_path  = list(path)
                    new_path.append(neighbour)
                    queue.append(new_path)
                    #return path if neighbour is centrenode
                    if neighbour == goal:
                        return new_path
                explored.append(node)