from classes.Player import Player

class Batter(Player):
    def __init__(self, id: int, team_abbreviation: str, order: int) -> None:
        super().__init__(id, team_abbreviation)
        self.order: int = order
        self.name: str = None
        self.pa: int = None  # plate appearances
        self.h: int = None  # hits
        self.h_per_pa: float = None  # hits per plate appearance
        self.h_per_pa_normalized: float = None
        self.evaluate: float = None
        self.evaluation: float = None  # h_per_bf * h_per_pa * team_h_per_pa * implied * total

    def set_stats(self, player_json: dict) -> None:
        self.pa = player_json["ap"]
        self.h = player_json["onbase"]['h']
        self.h_per_pa = self.h / self.pa if self.pa else 0
