# Player class for assignment
from BasePlayer import BasePlayer
import Command
import pdb
import copy

 

class Player(BasePlayer):

    def __init__(self):
        super().__init__()

        self.player_info = {}
        self.research_markets = []
        self.inventory_tracker = {}
        self.turn_tracker = 0
        self.visited_markets = {}

        self.black_market = None
        self.grey_market = None
    
    def take_turn(self, location, this_market, info, bm, gm):

        self.turn_tracker += 1
        self.black_market = copy.deepcopy(bm)
        self.grey_market = copy.deepcopy(gm)
        path = self.shortest_path(location, self.centrenode())
        if (len(path) > 1):
            path.pop(0)

        # Adds information from any players inside the market
        for m in info.keys():
            self.player_info[m] = info[m]


        priority_goals = sorted(self.goals_not_achieved(), key= lambda x: this_market.get(x,(999999,0))[0] * 
                                    abs(self.goal[x] - self.inventory_tracker.get(x,(0,0))[0]))
        print("PRIORITYGOALS",priority_goals)

        # if self.turn_tracker == 299:
        #     pdb.set_trace()

        if (location in (bm + gm)):
            return (Command.MOVE_TO, path[0])
        elif location not in self.research_markets:
            self.research_markets.append(location)
            return (Command.RESEARCH, None)
        else:
            # Checking if next node on path has cheaper options for cheapest goal
            if (len(path) > 1 and path[0] in (self.player_info.keys()) and
                path[0] not in (bm + gm)):
                first_goal = priority_goals[0]
                if (this_market[first_goal][0] > self.player_info[path[0]]):
                    return (Command.MOVE_TO,path[0])

            for goal in priority_goals:
                amount = min(self.goal[goal], this_market.get(goal,(9999,9999))[1], self.goal[goal] - self.inventory_tracker.get(goal,(0,0))[0])
                if (this_market[goal][0] * amount  < min(10000, self.gold) ):
                    self.inventory_tracker[goal] = (self.inventory_tracker.get(goal,(0,0))[0] + amount, this_market[goal][0])
                    self.gold -= amount * this_market[goal][0]
                    return (Command.BUY, (goal,amount))
            
                # if (this_market[goal][0] * amount  < 10000 - (amount * self.goal[goal])):
                #     return (Command.BUY, (goal,amount))

        return (Command.MOVE_TO, path[0])    








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
            # suggest that we only add those not in gray or black market to the targetnodelist
            if node not in self.black_market and node not in self.grey_market:
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
            return [location]
        
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

    def goals_achieved(self):
        """
        Helper to return goals achieved.
        """

        return [goal for goal in self.goal.keys() if  self.goal_met(goal)]

    def goals_not_achieved(self):
        """
        Helper to return all goals not yet achieved.
        """
        return [goal for goal in self.goal.keys() if not self.goal_met(goal)]

    def goal_met(self, goal_item):
        """
        Helper to check whether a goal item has been achieved.
        """ 
        return self.inventory_tracker.get(goal_item,(0,0))[0] >= \
                self.goal[goal_item]