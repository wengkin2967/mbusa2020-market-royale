# Player class for the assignment
from BasePlayer import BasePlayer
from Game import Game
import Command

class DummyPlayer(BasePlayer):
    """Minimal player."""

    def take_turn(self, location, prices, info, bm, gm):
        return (Command.PASS, None)

