import Command
from Map import Map
from BasePlayer import BasePlayer
import Market
import heapq as hq
import copy
from Priority_q_node import pq_node
class Player(BasePlayer):
    def __init__(self, mode='AVG', max_depth=50):
        super().__init__()
        self.package = {}
        self.mode = mode
        self.max_depth = max_depth

    def get_reward(self, node, action):
        if node.parent is None:
            pass
        pass
    def simulate_map(self, node, action):
        pass

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

        # return (Command.BUY, (this_market.keys()[0], this_market.values()[1]))  # example BUY
    def simple_dijkstra(self, loc, this_market, info, black_markets, grey_markets):
        priority_q = hq.heapify([])
        used_node = []
        potential = self.potential_action()
        for action in potential:
            node = pq_node()
            node.first_node(self, action)
            hq.heappush(priority_q, node)
        while priority_q:
            current_node = hq.heappop(priority_q)



    def potential_action(self):
        pass

        
if __name__ == "__main__":

    a = pq_node()
    a.first_node(Player(), 'action')
    b = pq_node()
    b.create_node(Player(), a,'action')
    print(a > b)
    print(a < b)
    print(a == b)
    c = []
    hq.heappush(c, a)
    hq.heappush(c, b)
    print(hq.heappop(c).depth)
    print(hq.heappop(c).depth)
    print(hq.heappop(c))
