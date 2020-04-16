# Player class for the assignment
from BasePlayer import BasePlayer

class Player(BasePlayer):
    pass;


player =  Player()
print(player)
player.set_gold(10000.0)
print(player.gold)

print("Hello")