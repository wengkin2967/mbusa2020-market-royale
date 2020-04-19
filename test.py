from Player import Player
from Game import Game

p1 = Player()
p2 = Player()
g = Game([p1,p2], verbose=True)
p1_scores = []
p2_scores = []
res =g.run_game()
print(res)
# for i in range(50):
    # res = g.run_game()
    # p1_scores.append(res[0])
    # p2_scores.append(res[1])

# print("Average for player 1: {}".format(sum(p1_scores)/len(p1_scores)))
# print("Average for player 2: {}".format(sum(p2_scores)/len(p2_scores)))