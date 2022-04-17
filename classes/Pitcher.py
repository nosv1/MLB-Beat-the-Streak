from classes.Player import Player

class Pitcher(Player):
    def __init__(self, id: int, team_abbreviation: str, name: str = None) -> None:
        super().__init__(id, team_abbreviation, name)
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

    def set_stats_starting_pitcher(self, pitcher_json: dict) -> None:
        self.bf = pitcher_json["bf"]

        self.h = pitcher_json['onbase']["h"]
        self.h_per_bf = self.h / self.bf if self.bf else 0

        self.bb = pitcher_json['onbase']["bb"]
        self.bb_per_bf = self.bb / self.bf if self.bf else 0

        self.k = pitcher_json["outs"]["ktotal"]
        self.k_per_bf = self.k / self.bf if self.bf else 0

    def set_stats_bullpen(self, pitcher_json: dict) -> None:
        # whip tells you how many extra batters you face per inning, so 3 outs + that is bf/ip, then x ip to get total bf
        self.bf = 3 + float(pitcher_json["whip"]) * self.parse_innings_pitched(pitcher_json["ip"])

        self.h = pitcher_json['h']
        self.h_per_bf = self.h / self.bf if self.bf else 0

        self.bb = pitcher_json['bb']
        self.bb_per_bf = self.bb / self.bf if self.bf else 0

        self.k = pitcher_json["k"]
        self.k_per_bf = self.k / self.bf if self.bf else 0

    def parse_innings_pitched(self, innings_pitched: str) -> float:
        return float(innings_pitched.replace(".1", str(1/3)[1:]).replace(".2", str(2/3)[1:]))