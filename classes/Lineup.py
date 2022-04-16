from classes.Batter import Batter
from classes.Pitcher import Pitcher
from classes.Bullpen import Bullpen

class Lineup:
    def __init__(self) -> None:
        self.starting_pitcher: Pitcher = None
        self.bullpen: Bullpen = Bullpen()
        self.batters: list[Batter] = []
        self.confirmed: bool = False