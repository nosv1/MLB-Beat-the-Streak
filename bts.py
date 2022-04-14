import json
import pickle
import requests 
import statistics
import os
import sys
import traceback

from collections import namedtuple
from datetime import datetime, timedelta
from itertools import chain
from selenium import webdriver

from classes.Batter import Batter
from classes.Game import Game
from classes.Pitcher import Pitcher
from classes.Team import Team


def games_decoder(games):
    return namedtuple("Games", games.keys())(*games.values())

def get_games(browser: webdriver.Chrome, date_string: str) -> list[Game]:
    # date_string in format YYYYMMDD

    print(f"Getting games for {date_string}...")

    url: str = f"https://api.actionnetwork.com/web/v1/scoreboard/mlb?date={date_string}"
    browser.get(url)
    games_json = json.loads(browser.find_element_by_tag_name("body").text)

    games: list[Game] = []

    for g in games_json['games']:
        games.append(
            Game(
                id=g["id"],
                start_time=g["start_time"],
                away_team_id=g["away_team_id"],
                home_team_id=g["home_team_id"]
            )
        )

    return games

def process_h_per_pa(games: list[Game]) -> list[Batter]:

    batters: list[Batter] = []

    for game in games:
        for team in game.teams:
            for batter in team.lineup.batters:
                if batter.pa:
                    batters.append(batter)

    # sort batters by plate appearances
    batters.sort(key=lambda b: b.pa, reverse=True)

    # get the top 75% plate appearances
    batters = batters[:int(len(batters) * 0.75)]
    print(f"Top 75% plate appearances: {batters[-1].pa}")

    # normalize hits per plate appearance
    h_per_pa: list[float] = [b.h_per_pa for b in batters]
    min_h_per_pa: float = min(h_per_pa)
    max_h_per_pa: float = max(h_per_pa)

    for batter in batters:
        batter.h_per_pa_normalized = (batter.h_per_pa - min_h_per_pa) / (max_h_per_pa - min_h_per_pa)

    batters.sort(key=lambda b: b.h_per_pa_normalized, reverse=True)
    json.dump(batters, open("stats/h_per_pa.json", "w"), indent=4, default=lambda o: o.__dict__)
    print(f"Processed hits per plate appearances...")

    return batters

def process_h_per_bf(games: list[Game]) -> list[Pitcher]:

    pitchers: list[Pitcher] = []

    for game in games:
        for team in game.teams:
            if team.lineup.starting_pitcher.bf:
                pitchers.append(team.lineup.starting_pitcher)

    # sort pitchers by bf
    pitchers.sort(key=lambda p: p.bf, reverse=True)

    # get the top 75% bf
    pitchers = pitchers[:int(len(pitchers) * 0.75)]
    print(f"Top 75% bf: {pitchers[-1].bf}")

    # normalize hits per bf
    h_per_bf: list[float] = [p.h_per_bf for p in pitchers]
    min_h_per_bf: float = min(h_per_bf)
    max_h_per_bf: float = max(h_per_bf)

    for pitcher in pitchers:
        pitcher.h_per_bf_normalized = (pitcher.h_per_bf - min_h_per_bf) / (max_h_per_bf - min_h_per_bf)

    pitchers.sort(key=lambda p: p.h_per_bf_normalized, reverse=True)
    json.dump(pitchers, open("stats/h_per_bf.json", "w"), indent=4, default=lambda o: o.__dict__)
    print(f"Processed hits per bf...")

    return pitchers

def process_team_h_per_pa(games: list[Game]) -> list[Team]:

    teams: list[Team] = []

    for game in games:
        teams += game.teams

    # normalize hits per plate appearance
    h_per_pa: list[float] = list(chain.from_iterable([[b.h_per_pa for b in team.lineup.batters if b.h_per_pa_normalized] for team in teams]))
    min_h_per_pa: float = min(h_per_pa)
    max_h_per_pa: float = max(h_per_pa)

    for team in teams:
        team.h_per_pa_normalized = (team.lineup.batters[0].h_per_pa - min_h_per_pa) / (max_h_per_pa - min_h_per_pa)

    teams.sort(key=lambda t: t.h_per_pa_normalized, reverse=True)
    json.dump(teams, open("stats/h_per_pa_teams.json", "w"), indent=4, default=lambda o: o.__dict__)
    print(f"Processed team hits per plate appearances...")

def process_team_total(games: list[Game]) -> list[Team]:

    teams: list[Team] = []

    for game in games:
        for team in game.teams:
            if team.odds.total:
                teams.append(team)

    # normalize total
    total: list[float] = [t.odds.total for t in teams]
    min_total: float = min(total)
    max_total: float = max(total)

    for team in teams:
        team.odds.total_normalized = (team.odds.total - min_total) / (max_total - min_total)

    teams.sort(key=lambda t: t.odds.total_normalized, reverse=True)
    json.dump(teams, open("stats/total_teams.json", "w"), indent=4, default=lambda o: o.__dict__)
    print(f"Processed team total...")

def process_team_moneyline(games: list[Game]) -> list[Team]:

    teams: list[Team] = []

    for game in games:
        for team in game.teams:
            if team.odds.moneyline:
                teams.append(team)

    # normalize moneyline
    implied: list[float] = [t.odds.implied for t in teams]
    min_implied: float = min(implied)
    max_implied: float = max(implied)

    for team in teams:
        team.odds.implied_normalized = (team.odds.implied - min_implied) / (max_implied - min_implied)


    teams.sort(key=lambda t: t.odds.implied_normalized, reverse=True)
    json.dump(teams, open("stats/moneyline_teams.json", "w"), indent=4, default=lambda o: o.__dict__)
    print(f"Processed team moneyline...")

def evaluate_batters(games: list[Game]) -> list[Batter]:

    batters: list[Batter] = []

    for game in games:
        for i, team in enumerate(game.teams):
            for batter in team.lineup.batters:
                if batter.order <= 3 and batter.h_per_pa_normalized and batter.h_per_pa_normalized > 0.5:
                    batter.evaluate = {
                        "h_per_pa": batter.h_per_pa_normalized,
                        "h_per_bf": game.teams[-1].lineup.starting_pitcher.h_per_bf_normalized if game.teams[-1].lineup.starting_pitcher.h_per_bf_normalized else .5,
                        "team_h_per_pa": team.h_per_pa_normalized if team.h_per_pa_normalized else .5,
                        "total": team.odds.total_normalized if team.odds.total_normalized else .5,
                        "implied": team.odds.implied_normalized if team.odds.implied_normalized else .5
                    }
                    batter.evaluation = statistics.mean(list(batter.evaluate.values()))
                    batters.append(batter)
            
    batters.sort(key=lambda b: b.evaluation, reverse=True)
    json.dump(batters, open("stats/evaluation.json", "w"), indent=4, default=lambda o: o.__dict__)
    print(f"Evaluated batters...")

def main(args):

    if args[0] == "games":

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        browser = webdriver.Chrome(options=options)

        try:
            
            d: datetime = datetime.now() + timedelta(days=0)
            date_string = d.strftime("%Y%m%d")
            print(f"Date: {d.strftime('%B %d, %Y')}")

            games: list[Game] = get_games(browser, date_string)

            for game in games:
                game.get_game_details(browser)

            pickle.dump(games, open("games.pkl", "wb"))
            json.dump(games, open(f"games/games_{date_string}.json", "w"), indent=4, default=lambda o: o.__dict__)
            print("Dumped games...")
        
        except Exception as e:
            print(traceback.format_exc())

        browser.close()

        args[0] = "stats"

    if args[0] == "stats":
        games: list[Game] = pickle.load(open(f"games.pkl", "rb"))

        batters: list[Batter] = process_h_per_pa(games)
        pitchers: list[Pitcher] = process_h_per_bf(games)
        h_per_pa_teams: list[Team] = process_team_h_per_pa(games)
        total_teams: list[Team] = process_team_total(games)
        moneyline_teams: list[Team] = process_team_moneyline(games)

        batters: list[Batter] = evaluate_batters(games)

if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)