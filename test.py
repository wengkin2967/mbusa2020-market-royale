from Player import Player
from DummyPlayer import DummyPlayer
from Game import Game
import sys

def run_test(ver = 'single', iterations = 100):
    if ver == 'single':
        p1 = Player()
        p2 = DummyPlayer()
        p3 = DummyPlayer()
        p4 = DummyPlayer()
        p5 = DummyPlayer()
        p6 = DummyPlayer()
        p7 = DummyPlayer()
        g = Game([p1,p2,p3,p4,p5,p6,p7], verbose=True)
        res = g.run_game(num_turns= 50)
        print(res)
    elif ver == 'avg':
        p_scores = [[] for i in range(7)]

        for i in range(iterations):
            p1 = Player()
            p2 = DummyPlayer()
            p3 = DummyPlayer()
            p4 = DummyPlayer()
            p5 = DummyPlayer()
            p6 = DummyPlayer()
            p7 = DummyPlayer()

            g = Game([p1,p2,p3,p4,p5,p6,p7], verbose=False)
            res = g.run_game(num_turns= 50)
            p_scores[0].append(res[0])
            p_scores[1].append(res[1])
            p_scores[2].append(res[2])
            p_scores[3].append(res[3])
            p_scores[4].append(res[4])
            p_scores[5].append(res[5])
            p_scores[6].append(res[6])


        for j in range(7):
            print("Average for player {}: {}".format(j+1,sum(p_scores[j])/len(p_scores[j])))
            print("Score range for player {}: ({},{})".format(j+1,min(p_scores[j]),max(p_scores[j])))


if len(sys.argv) == 3:
    run_test(sys.argv[1],int(sys.argv[2]))
elif len(sys.argv) == 2:
    run_test(sys.argv[1])
else:
    run_test()