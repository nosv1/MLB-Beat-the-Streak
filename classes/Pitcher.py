from classes.Player import Player

class Pitcher(Player):
    def __init__(self, id: int, team_abbreviation: str) -> None:
        super().__init__(id, team_abbreviation)
        self.bf: float = None  # batters faced

        self.h: int = None  # hits allowed 
        self.h_per_bf: float = None  # hits allowed per batters faced
        self.h_per_bf_normalized: float = None

        self.bb: int = None  # walks allowed
        self.bb_per_bf: float = None  # walks allowed per batters faced
        self.bb_per_bf_normalized: float = None

        self.k: int = None # strikeouts
        self.k_per_bf: float = None # strikeouts per batters faced
        self.k_per_bf_normalized: float = None

    def set_stats(self, player_json: dict) -> None:
        self.bf = player_json["bf"]

        self.h = player_json['onbase']["h"]
        self.h_per_bf = self.h / self.bf if self.bf else 0

        self.bb = player_json['onbase']["bb"]
        self.bb_per_bf = self.bb / self.bf if self.bf else 0

        self.k = player_json["outs"]["ktotal"]
        self.k_per_bf = self.k / self.bf if self.bf else 0