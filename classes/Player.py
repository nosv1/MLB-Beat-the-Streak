class Player:
    def __init__(self, id: int, team_abbreviation: str) -> None:
        self.id: int = id
        self.team_abbreviation: str = team_abbreviation

    def set_player_name(self, players_json: list[dict]) -> None:
        for player in players_json:
            if player["id"] == self.id:
                self.name = player["full_name"]
                break