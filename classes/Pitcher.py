from classes.Player import Player

class Pitcher(Player):
    def __init__(self, id: int, team_abbreviation: str) -> None:
        super().__init__(id, team_abbreviation)
        self.bf: float = None  # batters faced
        self.h: int = None  # hits allowed 
        self.h_per_bf: float = None  # hits allowed per batters faced
        self.h_per_bf_normalized: float = None

    def to_string(self) -> str:
        return f"{self.name} ({self.ip} IP, {self.h} H, {self.h_ip} H/IP)"

    def set_stats(self, player_json: dict) -> None:
        self.bf = player_json["bf"]
        self.h = player_json['onbase']["h"]
        self.h_per_bf = self.h / self.bf if self.bf else 0