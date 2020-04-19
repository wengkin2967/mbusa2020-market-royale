from Player import Player
from DummyPlayer import DummyPlayer
from Game import Game
import sys

def run_test(ver = 'single'):
    if ver == 'single':
        p1 = Player()
        p2 = DummyPlayer()
        g = Game([p1,p2], verbose=True)
        res = g.run_game()
        print(res)
    elif ver == 'avg':
        p1_scores = []
        p2_scores = []
        for i in range(200):
            p1 = Player()
            p2 = DummyPlayer()
            g = Game([p1,p2], verbose=False)
            res = g.run_game()
            p1_scores.append(res[0])
            p2_scores.append(res[1])

        print("Average for player 1: {}".format(sum(p1_scores)/len(p1_scores)))
        print("Average for player 2: {}".format(sum(p2_scores)/len(p2_scores)))


if len(sys.argv) > 1:
    run_test(sys.argv[1])
else:
    run_test()