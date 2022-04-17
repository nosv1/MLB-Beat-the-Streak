class Player:
    def __init__(self, id: int, team_abbreviation: str, name: str = None) -> None:
        ''' 
        batter and pitcher id come from ActionNetwork, bullpen IDs come from rotowire
        '''
        self.id: int = id  
        self.team_abbreviation: str = team_abbreviation
        self.name: str = name

    def set_player_name(self, players_json: list[dict]) -> None:
        for player in players_json:
            if player["id"] == self.id:
                self.name = player["full_name"]
                break