import json

from difflib import get_close_matches
from selenium import webdriver
from statistics import mean

from classes.Batter import Batter
from classes.Lineup import Lineup
from classes.Odds import Odds
from classes.Pitcher import Pitcher


class Team:
    def __init__(self, id: int, name: str, abbreviation: str) -> None:
        self.id: int = id
        self.name: str = name
        self.abbreviation: str = abbreviation
        self.odds: Odds = None
        self.is_home: bool = None
        self.lineup: Lineup = Lineup()

        # all calculated in process stats
        self.h_per_pa: float = None  # hits per plate appearance
        self.h_per_pa_normalized: float = None

        self.bb_per_pa: float = None  # walks per plate appearance
        self.bb_per_pa_normalized: float = None

        self.k_per_pa: float = None  # strikeouts per plate appearance
        self.k_per_pa_normalized: float = None

    def get_lineup(self, game_json: dict) -> None:

        print(f"Getting {self.abbreviation} lineup...", end="")

        # starting batters only
        for player in game_json["lineups"]["home" if self.is_home else "away"]:

            # starting lineup
            if player["inning"] == 0:

                # starting pitcher
                if player["position"] == "P":

                    self.lineup.starting_pitcher = Pitcher(
                        id=player["player_id"],
                        team_abbreviation=self.abbreviation,
                    )
                    self.lineup.starting_pitcher.set_player_name(game_json["players"])

                else:
                    self.lineup.batters.append(
                        Batter(
                            id=player["player_id"],
                            team_abbreviation=self.abbreviation,
                            order=player["order"],
                        )
                    )
                    self.lineup.batters[-1].set_player_name(game_json["players"])

            else:
                break
    
        try:
            self.lineup.confirmed = bool(
                game_json["lineups"]["homeConfirmed" if self.is_home else "awayConfirmed"]
            )
        except KeyError:
            self.lineup.confirmed = False

        print(f" {'✓' if self.lineup.confirmed else '✗'}")

    def get_batting_stats(self, game_json: dict) -> None:

        with open("stats/batters.json", "r") as f:
            batters_json = json.load(f)

            for batter in self.lineup.batters:
                for player in game_json['player_season_stats']['home' if self.is_home else 'away']:
                    if player["player_id"] == batter.id:
                        batter_key = f"{batter.name} ({self.name})".upper()
                        batter.set_stats(player["hitting"], batters_json[batter_key])
                        break

    def get_pitching_stats(self, game_json: dict) -> None:

        for player in game_json['player_season_stats']['home' if self.is_home else 'away']:

            # starting pitcher
            if player["player_id"] == self.lineup.starting_pitcher.id:
                self.lineup.starting_pitcher.set_stats(player["pitching"])

            # bullpen, pitcher but no starts
            if player["pitching"] and not player["pitching"]["games"]["start"] and not player["hitting"]:
                pitcher = Pitcher(
                    id=player["player_id"],
                    team_abbreviation=self.abbreviation,
                )
                pitcher.set_player_name(game_json["players"])
                pitcher.set_stats(player["pitching"])
                self.lineup.bullpen.pitchers.append(pitcher)
        
        self.lineup.bullpen.set_stats()
    
    def set_odds(self, game_json: dict) -> None:

        moneylines: list[int] = []
        totals: list[float] = []

        for game_odds in game_json["odds"]:
            
            if game_odds["type"] == "game":

                moneyline = game_odds["ml_home" if self.is_home else "ml_away"]
                total = game_odds["home_total" if self.is_home else "away_total"]

                if moneyline:
                    moneylines.append(moneyline)

                if total:
                    totals.append(total)

        self.odds = Odds(
            moneyline=mean(moneylines),
            total=mean(totals),
        )