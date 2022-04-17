import json

from datetime import datetime
from pytz import timezone
from selenium import webdriver

from classes.Team import Team

class Game:
    def __init__(self, id: int, start_time: str, away_team_id: int, home_team_id: int) -> None:
        self.id: int = id
        self.start_time: str = timezone("UTC").localize(
            datetime.strptime(
                start_time, '%Y-%m-%dT%H:%M:%S.%fZ'
            )
        ).astimezone(
            timezone("America/Chicago")
        ).strftime(
            "%Y-%m-%d %I:%M %p"
        )
        self.url = f"https://api.actionnetwork.com/web/v1/games/{id}"
        self.away_team_id: int = away_team_id
        self.home_team_id: int = home_team_id
        self.teams: list[Team] = [None, None]
        self.total: float = None

    def get_game_details(self, browser: webdriver.Chrome) -> None:

        print(f"\nGetting game details {self.start_time} ({self.id})...")

        browser.get(self.url)
        game_json: dict = json.loads(browser.find_element_by_tag_name('body').text)

        self.get_teams(game_json)
        for team in self.teams:
            team.get_batting_stats(game_json)
            team.get_pitching_stats(game_json, browser)
            team.set_odds(game_json)
        
        self.total = game_json["odds"][0]["total"]

    def get_teams(self, game_json: dict) -> None:
        for i, team in enumerate(game_json["teams"]):

            t_team = Team(
                id=team["id"], 
                name=team["display_name"],
                abbreviation=team["abbr"]
            )

            if t_team.id == self.away_team_id:
                self.teams[0] = t_team
                self.teams[0].is_home = False
                self.teams[0].get_lineup(game_json)

            elif t_team.id == self.home_team_id:
                self.teams[1] = t_team
                self.teams[1].is_home = True
                self.teams[1].get_lineup(game_json)