import copy
class pq_node:
    def __init__(self):
        self.empty =True
        self.depth = None
        self.priority = None
        self.action = None
        self.parent = None
        self.reward = None
        self.acc_reward = None
        self.num_of_childs = 0
        self.status = None
    
    def __eq__(self, other):
        return self.priority == other.priority

    def __lt__(self,other):
        return self.priority < other.priority

    def __gt__(self, other):
        return self.priority > other.priority

    def first_node(self, action):
        self.empty = False
        self.depth = 1
        self.priority = self.depth
        self.action = action
        self.parent = None
        self.num_of_childs = 0
        self.acc_reward = 0
        
    
    def sub_node(self, parent, action):
        self.empty = False
        self.depth = parent.depth + 1
        self.priority = self.depth
        self.num_of_childs = 0
        self.action = action
        self.parent = parent
        self.acc_reward = parent.acc_reward
        #self.status = player.simulate_map(self, action)
        
        while parent is not None:
            parent.num_of_childs += 1
            parent = parent.parent

    def set_value(self, new_acc_reward, status):
        self.status = status
        self.reward = new_acc_reward - self.acc_reward
        self.acc_reward = new_acc_reward