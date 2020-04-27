# BUSA90500 2020 Battle Royal
# Author: Dengke Sha
# Date: 2020.03.31
#
# (Objectified and extended by Andrew Turpin 11 Apr 2020)
#

import random
from collections import defaultdict
import string

MIN_CIRCLE_UNSET = -1 # A value for signifying minimum circle parameters have not been set.

class Map():
    # Constants for indicating status of circle.
    NODE_STATUS_WHITE = 0
    NODE_STATUS_GREY = 1
    NODE_STATUS_BLACK = 2

    NODE_STATUS_GREY_ICON = "/"
    NODE_STATUS_BLACK_ICON = "#"


    EMPTY_ICON = " "
    PATH_ICON = "."
    

    def __init__(self, node_positions, node_graph, map_width, map_height, resolution_x, resolution_y):
        '''
        Sets up map_data from pre-generated node_positions and node_graph data.
        Use for setting up a pre-generated map to use.

        @param node_positions ...
        @param node_graph ...

        @param map_width ...
        @param map_height ...
        @param resolution_x ..
        @param resolution_y ...

        Populates
            self.map_data['node_positions'][String name] = (lat, lon, circle_status)
            self.map_data['node_graph'][String name] = {n1. n2, ...n mm} # set of reachable node names
        '''

        self.map_data = {}
        self.map_width = map_width
        self.map_height = map_height
        self.resolution_x = resolution_x
        self.resolution_y = resolution_y

        self.map_data["node_positions"] = node_positions
        self.map_data["node_graph"] = node_graph

        self.init_circle()

        self.render_map()

    # Good seeds: (2354), 2360
    def __init__(self, node_list, map_width, map_height, resolution_x, resolution_y, seed=2360):
        '''
        Generates a map_data from a node_list provided.

        @param map_width ...
        @param map_height ...
        @param resolution_x ..
        @param resolution_y ...
        @param node_list List of node names

        Creates
            self.map_data['node_positions'][String name] = (x, y, circle_status)
            self.map_data['node_graph'][String name] = {n1. n2, ...n mm} # set of reachable node names
        '''

        # Seed the random generator.
        random.seed(seed)

        self.map_data = {}
        self.map_width = map_width
        self.map_height = map_height
        self.resolution_x = resolution_x
        self.resolution_y = resolution_y

        # First maps node_lists onto a 2D map.
        node_positions = {}
        for node in node_list:
            node_positions[node] = (random.random() * map_width, random.random() * map_height, Map.NODE_STATUS_WHITE)  # all start in circle

        self.map_data["node_positions"] = node_positions

        # Generate the underlying graph of the map (the paths).
        node_graph = defaultdict(set)

        # The number of outgoing edges we want to generate per node.
        outgoing_edges_min = 2
        outgoing_edges_max = 4
        

        for node in node_list:
            # Find the closest nodes (sorted by closest)
            #print("Finding closest nodes of " + node + "...")
            closest_other_nodes = []
            for other_node in node_list:
                if node != other_node: # Only calculate distance if not the same node.
                    (node_x, node_y, _) = node_positions[node]
                    (other_node_x, other_node_y, _) = node_positions[other_node]

                    dx = (node_x - other_node_x)
                    dy = (node_y - other_node_y)
                    distance = (dx ** 2 + dy ** 2) ** 0.5
                    closest_other_nodes.append((distance, other_node))

            closest_other_nodes.sort() # Sorts nodes from closest to furthest away.
            #print("Closest other nodes found:", closest_other_nodes)
            #print()
            
            # Generate a random number of outgoing edges, connecting them to closest other nodes.
            edges_outgoing_for_node = random.randint(outgoing_edges_min, outgoing_edges_max)
            for edge_i in range(edges_outgoing_for_node):
                # Create the relationship to map node to other_node (both ways).
                other_node = closest_other_nodes[edge_i][1]
                node_graph[node].add(other_node)
                node_graph[other_node].add(node)

        self.map_data["node_graph"] = node_graph

        self.init_circle()

        self.render_map()


    def init_circle(self):
        '''
        Initializes the circle.
        '''
        self.circle = {}
        self.circle['y_min'] = 0
        self.circle['y_max'] = self.map_height
        self.circle['x_min'] = 0
        self.circle['x_max'] = self.map_width

    def render_map(self):
        '''
        Takes in the self.map_data and produces a map_2d which is a pretty_printable
        visualization of the map.
        '''

        node_positions = self.map_data["node_positions"]

        # Number of blocks to represent x direction.
        x_blocks = int(self.map_width / self.resolution_x)
        y_blocks = int(self.map_height / self.resolution_y)

        # Initialize the map to be empty.
        self.map_2d = []
        for y in range(y_blocks):
            map_row = [] # An individual row of a map.
            for x in range(x_blocks):
                map_row.append(Map.EMPTY_ICON)
            self.map_2d.append(map_row)

        # The number of times we will sample the line to render the path
        SAMPLING_AMOUNT_PER_LINE = 10
        # For every node that connects to other_node
        node_graph = self.map_data["node_graph"]
        for node, other_nodes in node_graph.items():
            # Sample the edges to render the paths between nodes.
     
            for other_node in other_nodes:
                if node != other_node: # Only c (rise/run) if node not the same.
                    start_pos = node_positions[node][:2]
                    end_pos = node_positions[other_node][:2]
                    (dx, dy) = Map.dx_dy_between_pos(start_pos, end_pos)

                    #c = abs(dy / dx)

                    step_x = abs(dx/SAMPLING_AMOUNT_PER_LINE)
                    step_y = abs(dy/SAMPLING_AMOUNT_PER_LINE)

                    # Initialize where we start painting the path.
                    (node_x, node_y) = start_pos
                    current_path_x = node_x
                    current_path_y = node_y
                    # "Paint on" the path for all samples on the path.
                    distance_left_to_other_node = Map.distance_between_pos(start_pos, end_pos)
                    (end_x, end_y) = end_pos

                    distance_before_close_enough_to_destination = (step_x ** 2 + step_y ** 2) ** 0.5
                    while distance_left_to_other_node > distance_before_close_enough_to_destination:

                        # Move toward the end position.
                        if current_path_x < end_x:
                            current_path_x += step_x
                        else:
                            current_path_x -= step_x

                        if current_path_y < end_y:
                            current_path_y += step_y #* c
                        else:
                            current_path_y -= step_y #* c

                        self.set_map_2d_icon(current_path_x, current_path_y, Map.PATH_ICON)
                        
                        distance_left_to_other_node = Map.distance_between_pos((current_path_x, current_path_y), end_pos)
                        #print(current_path_x, current_path_y, node_positions[other_node], distance_left_to_other_node, STEP_SIZE)

        # Update the 2d array to have different icon to represent a point
        # of interest.
        for (node, (x, y, node_circle_status)) in node_positions.items():
            # Sets an icon at the map position, using a the first letter of
            # the node name.
            icon_for_node = node[0]

            # If the circle status is grey or black, change the icon.
            if node_circle_status == Map.NODE_STATUS_GREY:
                icon_for_node = Map.NODE_STATUS_GREY_ICON

            if node_circle_status == Map.NODE_STATUS_BLACK:
                icon_for_node = Map.NODE_STATUS_BLACK_ICON

            self.set_map_2d_icon(x, y, icon_for_node)


    def distance_between_pos(node_pos, other_node_pos):
        '''
        Calculates the distance between node positions (x, y), (x2, y2).
        '''
        (dx, dy) = Map.dx_dy_between_pos(node_pos, other_node_pos)

        distance = (dx ** 2 + dy ** 2) ** 0.5

        return distance

    def dx_dy_between_pos(node_pos, other_node_pos):
        '''
        Calculates the (dx, dy) between node positions (x, y), (x2, y2).
        '''

        (node_x, node_y) = node_pos
        (other_node_x, other_node_y) = other_node_pos

        dx = (node_x - other_node_x)
        dy = (node_y - other_node_y)

        return (dx, dy)

    def set_map_2d_icon(self, x, y, icon):
        '''
        Sets the icon for a particular position onto the 2d map representation.
        '''

        block_map_width = len(self.map_2d[0])
        block_map_height = len(self.map_2d)

        # Calculate the positions, as a block positions.
        x_block_pos = int(x / self.resolution_x)
        y_block_pos = int(y / self.resolution_y)


        # Has a safety check to prevent trying to set to a position out of range.
        if (x_block_pos < 0 or x_block_pos > block_map_width - 1 or
            y_block_pos < 0 or y_block_pos > block_map_height - 1):
            # Out of range, so just do nothing.
            #print("Out of range, not setting icon for map")
            #print(x_block_pos, y_block_pos, block_map_width, block_map_height)
            return

        # Sets an icon at the map position.
        self.map_2d[y_block_pos][x_block_pos] = icon
            
    def pretty_print_map(self):
        ''' Pretty prints the 2d map '''
        
        # Print out the map.
        for row in self.map_2d:
            print("".join(row))

        print()

    def pretty_print_node_positions(self):
        for (key, value) in self.map_data["node_positions"].items():
            print(key + ":", value)
        print()
        
    def pretty_print_node_graph(self):
        for (key, value) in self.map_data['node_graph'].items():
                print(key + ":", value)
        print()

    def pretty_print_dict(dictionary):
        '''
        General utility function for printing a dictionary prettily (better to
        use other more specific pretty print functions - use as last resort
        '''
        for (key, value) in dictionary.items():
            print(key)
            print("   ", value)
            print()

    def move_circle(self, num_turns_in_game, min_circle_width=MIN_CIRCLE_UNSET, min_circle_height=MIN_CIRCLE_UNSET): # move circle in one step and update node flags 
        '''
        Decreases the size of the circle each turn. Rate at which the circle decreases is
        based on the size of the map. Note that our circle is currently actually a rectangle.

        Circle closes toward the center of the map, at a constant rate.

        Note that this method assumes the circle is decreasing in size, so will not reset any "black"
        nodes to "white".

        @param num_turns_in_game The number of turns the full game will run for.
        @param min_circle_width Minimum width of the circle. Cirle will not decrease past this size.
        @param min_circle_height Minimum height of the circle. Cirle will not decrease past this size.
        '''

        # If min_circle_width or min_circle_height are MIN_CIRCLE_UNSET, set them to a default value.
        if min_circle_width == MIN_CIRCLE_UNSET:
            min_circle_width = self.map_width/4
        if min_circle_height == MIN_CIRCLE_UNSET:
            min_circle_height = self.map_height/4

        node_positions = self.map_data['node_positions']

        # First, check to see if any nodes are "grey". If so, set them to "black".
        for (node_name, (node_x, node_y, node_circle_status)) in node_positions.items():
            #(node_x, node_y, node_circle_status) = node_positions[node_name]
            
            if node_circle_status == Map.NODE_STATUS_GREY:
                node_positions[node_name] = (node_x, node_y, Map.NODE_STATUS_BLACK)

        # Decrease the circle. The decrease in rate by a factor of 2 is because we decrease from both directions
        # at once, which doubles the rate of decrease. This is to offset that.
        circle_decrease_amount_x_per_turn = (self.map_width / 2) / num_turns_in_game
        circle_decrease_amount_y_per_turn = (self.map_height / 2) / num_turns_in_game

        self.circle['x_min'] += circle_decrease_amount_x_per_turn
        self.circle['x_max'] -= circle_decrease_amount_x_per_turn
        self.circle['y_min'] += circle_decrease_amount_y_per_turn
        self.circle['y_max'] -= circle_decrease_amount_y_per_turn

        # Cap circle at minimum size.
        if self.circle['x_max'] - self.circle['x_min'] < min_circle_width:
            self.circle['x_min'] = (self.map_width / 2) - min_circle_width / 2
            self.circle['x_max'] = (self.map_width / 2) + min_circle_width / 2

        if self.circle['y_max'] - self.circle['y_min'] < min_circle_height:
            self.circle['y_min'] = (self.map_height / 2) - min_circle_height / 2
            self.circle['y_max'] = (self.map_height / 2) + min_circle_height / 2

        # For each node, check to see if they will be within the new circle.
        for node_name in node_positions.keys():
            (node_x, node_y, node_circle_status) = node_positions[node_name]
            
            # Checks for left, right, up, down edges of circle.
            if node_x <= self.circle['x_min'] or node_x >= self.circle['x_max'] or node_y <= self.circle['y_min'] or node_y >= self.circle['y_max']:
                
                if node_circle_status != Map.NODE_STATUS_BLACK:
                    # Outside circle. Set the node to grey. Don't change to grey if already black.
                    node_positions[node_name] = (node_x, node_y, Map.NODE_STATUS_GREY)

    def get_node_names(self): return list(self.map_data['node_positions'].keys())

    def get_neighbours(self, node): 
        """@param node str name of node/location in map
           @return List of string names of direct neighbours of node.
        """
        assert(node in self.map_data['node_graph'])
        return self.map_data['node_graph'][node]

    def is_road(self, n1, n2):
        """@return True if n2 is an immediate neighbour of n1.
        """
        if n1 not in self.map_data['node_graph']:
            return False
        return n2 in self.map_data['node_graph'][n1]

    def outside_circle(self, node): 
        """@return True if node does not exist, or is outside circle. False otherwise.
        """
        if node not in self.map_data['node_positions']:
            return True
        return self.map_data['node_positions'][node][2] == Map.NODE_STATUS_BLACK

    def get_node_status(self):
        """@return list of (node_name, status) tuples.
        """
        return [(node, color) for (node, (_, _, color)) in self.map_data['node_positions'].items()]

if __name__ == "__main__":

    # Test code
    map_width = 200 # Dimensions of map
    map_height = 100
    resolution_x = 2 # Resolution to render the map at
    resolution_y = 3

    # Simple map
    # node_list = ["Academy", "City", "Gallery", "Junkyard", "Office", "Park", "Stadium", "Tree", "Weather Station"]
    # map = Map(node_list, map_width, map_height, resolution_x, resolution_y, seed=2354)
    
    # Medium map
    node_list = list(string.ascii_uppercase)
    map = Map(node_list, map_width, map_height, resolution_x, resolution_y, seed=23624)

    # Large map
    #node_list = list(string.ascii_uppercase) + list(string.ascii_lowercase)
    #map = Map(node_list, map_width, map_height, resolution_x, resolution_y, seed=2360)

    print('map_data["node_positions"]')
    map.pretty_print_node_positions()
    print('map_data["node_graph"]')
    map.pretty_print_node_graph()

    map.pretty_print_map()
