from classes.Batter import Batter
from classes.Pitcher import Pitcher

class Lineup:
    def __init__(self) -> None:
        self.starting_pitcher: Pitcher = None
        self.batters: list[Batter] = []
        self.confirmed: bool = False