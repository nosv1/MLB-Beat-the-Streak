# parse boxscores in boxscores/{date_string}/{game_id}.json

import json
import os

from dataclasses import dataclass


@dataclass
class Batter:
    name: str
    team_name: str
    ofers: int = 0
    games: int = 0
    ofers_per_game: float = None

    def to_dict_key(self):
        return f"{self.name.upper()} ({self.team_name.upper()})"

def parse_boxscore(boxscore_path: str, batters: dict[str, Batter]) -> dict[str, Batter]:

    with open(boxscore_path) as f:
        boxscore_json = json.load(f)

        for team in boxscore_json:
            team_name = team['title'].title()

            for row in team["boxscoreItems"][0]["boxscoreTable"]["rows"]:

                if "entityLink" not in row:
                    break

                batter = Batter(
                    name=row["entityLink"]["title"].title(),
                    team_name=team_name
                )

                batter_key = batter.to_dict_key()
                # check if batter_key is not in batters
                if batter_key not in batters:
                    batters[batter_key] = batter

                batters[batter_key].games += 1
                batters[batter_key].ofers += 1 if row["columns"][3]["text"] == "0" else 0
                batters[batter_key].ofers_per_game = (
                    batters[batter_key].ofers / batters[batter_key].games
                )

    return batters


def main():
    batters: dict[str, Batter] = {} # {name (team_abbreviation): Batter}

    for date_string in os.listdir('boxscores'):
        for game_id in os.listdir(f'boxscores/{date_string}'):
            boxscore_path = f'boxscores/{date_string}/{game_id}'
            batters = parse_boxscore(boxscore_path, batters)

    # sort batters by ofers_per_game asc then by games desc
    batters = {
        batter.to_dict_key(): batter
        for batter in sorted(
            list(batters.values()),
            key=lambda batter: (batter.ofers_per_game, -batter.games)
        )
    }

    json.dump(batters, open('stats/batters.json', 'w'), indent=4, default=lambda o: o.__dict__)

if __name__ == "__main__":
    main()