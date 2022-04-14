import json
import os

from dataclasses import dataclass

@dataclass
class Batter:
    name: str
    lineup_positions: list[int]

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Batter):
            return False
        return self.name == __o.name

@ dataclass
class Team:
    abbreviation: str
    batters: list[Batter] = None

team_lineup_history: dict[str, Team] = {}

# loop .json files in games folder
for filename in os.listdir('games'):
    games = json.load(open(os.path.join('games', filename)))

    for game in games:

        home = game['home']
        away = game['away']

        temp_teams = [game['home'], game['away']]

        for team in temp_teams:

            if team['abbreviation'] not in team_lineup_history:
                team_lineup_history[team['abbreviation']] = Team(
                    abbreviation=team['abbreviation'],
                    batters=[]
                )

            for i, batter in enumerate(team['lineup']['batters']):
                batter = Batter(
                    name=batter['name'],
                    lineup_positions=[batter['lineup_position']]
                )
                if batter not in team_lineup_history[team['abbreviation']].batters:
                    team_lineup_history[team['abbreviation']].batters.append(batter)
                else:
                    team_lineup_history[team['abbreviation']].batters[team_lineup_history[team['abbreviation']].batters.index(batter)].lineup_positions.append(batter.lineup_positions[-1])

for abbreviation, team in team_lineup_history.items():

    json.dump(team, open(f"data/lineup_history_{abbreviation}.json", 'w'), indent=4, default=lambda o: o.__dict__)
