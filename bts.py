import json
import pickle
import requests 
import statistics
import os
import sys
import traceback

from datetime import datetime, timedelta
from itertools import chain
from selenium import webdriver

from classes.Batter import Batter
from classes.Game import Game
from classes.Pitcher import Pitcher
from classes.Team import Team


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

def process_h_bb_k_per_pa(games: list[Game]) -> list[Batter]:

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
    per_pa: dict[str, list[float]] = {"h": [], "k": [], "bb": []}
    for b in batters:
        per_pa["h"].append(b.h_per_pa)
        per_pa["bb"].append(b.bb_per_pa)
        per_pa["k"].append(b.k_per_pa)

    min_h_per_pa: float = min(per_pa["h"])
    max_h_per_pa: float = max(per_pa["h"])

    min_bb_per_pa: float = min(per_pa["bb"])
    max_bb_per_pa: float = max(per_pa["bb"])

    min_k_per_pa: float = min(per_pa["k"])
    max_k_per_pa: float = max(per_pa["k"])

    for batter in batters:
        batter.h_per_pa_normalized = (batter.h_per_pa - min_h_per_pa) / (max_h_per_pa - min_h_per_pa)
        batter.bb_per_pa_normalized = 1 - (batter.bb_per_pa - min_bb_per_pa) / (max_bb_per_pa - min_bb_per_pa)
        batter.k_per_pa_normalized = 1 - (batter.k_per_pa - min_k_per_pa) / (max_k_per_pa - min_k_per_pa)

    batters.sort(key=lambda b: b.h_per_pa_normalized, reverse=True)
    json.dump(batters, open("evaluations/batters_h_per_pa.json", "w"), indent=4, default=lambda o: o.__dict__)

    batters.sort(key=lambda b: b.bb_per_pa_normalized, reverse=True)
    json.dump(batters, open("evaluations/batters_bb_per_pa.json", "w"), indent=4, default=lambda o: o.__dict__)

    batters.sort(key=lambda b: b.k_per_pa_normalized, reverse=True)
    json.dump(batters, open("evaluations/batters_k_per_pa.json", "w"), indent=4, default=lambda o: o.__dict__)

    print(f"Processed hits, bbs, and ks per plate appearances...")

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
    json.dump(pitchers, open("evaluations/pitchers_h_per_bf.json", "w"), indent=4, default=lambda o: o.__dict__)
    print(f"Processed hits per bf...")

    return pitchers

def process_team_h_bb_k_per_pa(games: list[Game]) -> list[Team]:

    teams: list[Team] = []

    for game in games:
        for team in game.teams:
            batters: list[Batter] = []
            for batter in team.lineup.batters:
                if batter.h_per_pa_normalized:
                    batters.append(batter)

            if len(batters) >= 5:
                team.h_per_pa = statistics.mean([b.h_per_pa for b in batters])
                team.bb_per_pa = statistics.mean([b.bb_per_pa for b in batters])
                team.k_per_pa = statistics.mean([b.k_per_pa for b in batters])
                teams.append(team)

    # normalize hits per plate appearance
    per_pa: dict[str, list[float]] = {"h": [], "k": [], "bb": []}
    for t in teams:
        per_pa["h"].append(t.h_per_pa)
        per_pa["bb"].append(t.bb_per_pa)
        per_pa["k"].append(t.k_per_pa)

    min_h_per_pa: float = min(per_pa["h"])
    max_h_per_pa: float = max(per_pa["h"])

    min_bb_per_pa: float = min(per_pa["bb"])
    max_bb_per_pa: float = max(per_pa["bb"])

    min_k_per_pa: float = min(per_pa["k"])
    max_k_per_pa: float = max(per_pa["k"])

    for team in teams:
        team.h_per_pa_normalized = (team.h_per_pa - min_h_per_pa) / (max_h_per_pa - min_h_per_pa)
        team.bb_per_pa_normalized = (team.bb_per_pa - min_bb_per_pa) / (max_bb_per_pa - min_bb_per_pa)
        team.k_per_pa_normalized = (team.k_per_pa - min_k_per_pa) / (max_k_per_pa - min_k_per_pa)

    teams.sort(key=lambda t: t.h_per_pa_normalized, reverse=True)
    json.dump(teams, open("evaluations/teams_h_per_pa.json", "w"), indent=4, default=lambda o: o.__dict__)

    teams.sort(key=lambda t: t.bb_per_pa_normalized, reverse=True)
    json.dump(teams, open("evaluations/teams_bb_per_pa.json", "w"), indent=4, default=lambda o: o.__dict__)

    teams.sort(key=lambda t: t.k_per_pa_normalized, reverse=True)
    json.dump(teams, open("evaluations/teams_k_per_pa.json", "w"), indent=4, default=lambda o: o.__dict__)


    print(f"Processed team hits, bbs, and ks per plate appearances...")

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
    json.dump(teams, open("evaluations/teams_total.json", "w"), indent=4, default=lambda o: o.__dict__)
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
    json.dump(teams, open("evaluations/teams_moneyline.json", "w"), indent=4, default=lambda o: o.__dict__)
    print(f"Processed team moneyline...")

def evaluate_batters(games: list[Game]) -> list[Batter]:

    batters: list[Batter] = []

    for game in games:
        for i, team in enumerate(game.teams):
            for batter in team.lineup.batters:
                if (
                    batter.order <= 6 and
                    batter.h_per_pa_normalized and 
                    game.teams[i - 1].lineup.starting_pitcher.h_per_bf_normalized and
                    team.h_per_pa_normalized and 
                    team.odds.total_normalized and 
                    team.odds.implied_normalized
                ):
                    batter.evaluate = {
                        "h_per_pa": (batter.h_per_pa_normalized) * 1.333,
                        "bb_per_pa": (batter.bb_per_pa_normalized) * 1.333,
                        "k_per_pa": (batter.k_per_pa_normalized) * 1.333,

                        "h_per_bf": (game.teams[i - 1].lineup.starting_pitcher.h_per_bf_normalized) * 1.5,

                        "team_h_per_pa": (team.h_per_pa_normalized) * 0.666,
                        "team_bb_per_pa": (team.bb_per_pa_normalized) * 0.666,
                        "team_k_per_pa": (team.k_per_pa_normalized) * 0.666,

                        "total": (team.odds.total_normalized) * 1.25,
                        "implied": (team.odds.implied_normalized) * 1.25
                    }
                    batter.evaluation = statistics.mean(list(batter.evaluate.values()))
                    batters.append(batter)
            
    batters.sort(key=lambda b: b.evaluation, reverse=True)
    json.dump(batters, open("evaluations/evaluation.json", "w"), indent=4, default=lambda o: o.__dict__)
    print(f"Evaluated batters...")

def main(args):

    if args[0] == "games":

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        browser = webdriver.Chrome(options=options)

        try:
            
            d: datetime = datetime.now() + timedelta(days=-1)
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

        batters: list[Batter] = process_h_bb_k_per_pa(games)
        pitchers: list[Pitcher] = process_h_per_bf(games)
        h_per_pa_teams: list[Team] = process_team_h_bb_k_per_pa(games)
        total_teams: list[Team] = process_team_total(games)
        moneyline_teams: list[Team] = process_team_moneyline(games)

        batters: list[Batter] = evaluate_batters(games)

if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)