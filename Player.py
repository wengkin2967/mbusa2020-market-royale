# Player class for the assignment
from BasePlayer import BasePlayer
from Game import Game
import Command

class Player(BasePlayer):
    """Minimal player."""
    
    def __init__(self):
        super().__init__()
        self.info_tracker = {}
        self.inventory_price_tracker = {}
    

    def take_turn(self, location, prices, info, bm, gm):
        if location in (bm or gm):
            for i in self.map.get_neighbours(location):
                if i not in bm or gm:
                    return(Command.MOVE_TO,i)
        return (Command.PASS, None)

p1 = Player()
p2 = Player()
g = Game([p1,p2], verbose=False)
p1_scores = []
p2_scores = []
res =g.run_game()
print(res)
for i in range(50):
    res = g.run_game()
    p1_scores.append(res[0])
    p2_scores.append(res[1])

print("Average for player 1: {}".format(sum(p1_scores)/len(p1_scores)))
print("Average for player 2: {}".format(sum(p2_scores)/len(p2_scores)))