from classes.Player import Player

class Batter(Player):
    def __init__(self, id: int, team_abbreviation: str, order: int) -> None:
        super().__init__(id, team_abbreviation)
        self.order: int = order
        self.name: str = None
        self.opposing_starting_pitcher_name: str = None

        self.pa: int = None  # plate appearances

        self.h: int = None  # hits
        self.h_per_pa: float = None  # hits per plate appearance
        self.h_per_pa_normalized: float = None

        self.bb: int = None  # walks
        self.bb_per_pa: float = None  # walks per plate appearance
        self.bb_per_pa_normalized: float = None

        self.k: int = None  # strikeouts
        self.k_per_pa: float = None  # strikeouts per plate appearance
        self.k_per_pa_normalized: float = None

        self.g: int = None  # games
        self.ofers_per_g: float = None  # ofers per game
        self.ofers_per_g_normalized: float = None

        self.evaluate: float = None
        self.evaluation: float = None  # h_per_bf * h_per_pa * team_h_per_pa * implied * total

    def set_stats(self, player_json: dict, batter_stats: dict) -> None:
        self.pa = player_json["ap"]

        self.h = player_json["onbase"]['h']
        self.h_per_pa = self.h / self.pa if self.pa else 0

        self.bb = player_json["onbase"]['bb']
        self.bb_per_pa = self.bb / self.pa if self.pa else 0

        self.k = player_json["outs"]['ktotal']
        self.k_per_pa = self.k / self.pa if self.pa else 0

        self.g = batter_stats["games"]
        self.ofers_per_g = batter_stats["ofers_per_game"]