# Player class for the assignment
from BasePlayer import BasePlayer
import Command
from Map import *
from Game import Game

p1 = Player()
p2 = Player()
    
g = Game([p1,p2],verbose = True)
res = g.run_game()
print(res)


class Player(BasePlayer):
    """Minimal Player"""
    def take_turn(self, location, prices, info, bm, gm):
    
        #Find the nodes within final safe circle: 
        white_nodes = []
        for node in self.Map.node_list:
            for (node, (node_x, node_y, _)) in self.Map.node_positions.items():
                if node_x in range(50,151) and node_y in range(25, 76):
                    white_nodes.append(node)
        
        #Find the the distances of all the other nodes to the current node:
        closest_other_nodes = []
        for other_node in self.Map.node_list:
            if location != other_node: #Only calculate distances for two different nodes
                (node_x, node_y, _) = self.Map.node_positions[location]
                (other_node_x, other_node_y, _) = self.Map.node_positions[other_node]
                
                dx = (node_x - other_node_x)
                dy = (node_y - other_node_y)
                distance = (dx ** 2 + dy ** 2) ** 0.5
                
                closest_other_nodes.append((distance, other_node))
                
        closest_other_nodes.sort()  #sort other nodes from the nearest to the furtherest
        
        #Find the closest node in the final safe circle to the current node:
        closest_white_nodes = []
        for (distance, other_node) in closest_other_nodes:
            if other_node in white_nodes:
                closest_white_nodes.append(other_node)
                
                ###If same distance, consider avoiding black market
        
        closest_white_node = closest_white_nodes[0]
            
        return (Command.MOVE_TO, closest_white_node)
        
        
                 
        
        
    
    
    
           

    #1.find the closet node within the circle
    #2. find all the paths to that node
    #3. move along the shortest path




