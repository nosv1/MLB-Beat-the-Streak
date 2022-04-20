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
from classes.Bullpen import Bullpen
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

def process_batters(games: list[Game]) -> list[Batter]:
    # batters h_per_pa
    # batters bb_per_pa
    # batters k_per_pa
    # batters ofers_per_g

    batters: list[Batter] = []

    for game in games:
        for team in game.teams:
            for batter in team.lineup.batters:
                if batter.pa:
                    batters.append(batter)

    # sort batters by plate appearances
    batters.sort(key=lambda b: b.pa, reverse=True)

    # get the top 80% plate appearances
    batters = batters[:int(len(batters) * 0.80)]
    print(f"Top 80% plate appearances: {batters[-1].pa}")

    # sort batters by games
    batters.sort(key=lambda b: b.g, reverse=True)

    # get the top 80% games
    batters = batters[:int(len(batters) * 0.80)]
    print(f"Top 80% games: {batters[-1].g}")

    # normalize hits per plate appearance
    per_pa: dict[str, list[float]] = {"h": [], "k": [], "bb": []}
    per_g: dict[str, list[float]] = {"ofers": []}
    for b in batters:
        per_pa["h"].append(b.h_per_pa)
        per_pa["bb"].append(b.bb_per_pa)
        per_pa["k"].append(b.k_per_pa)
        per_g["ofers"].append(b.ofers_per_g)

    min_h_per_pa: float = min(per_pa["h"])
    max_h_per_pa: float = max(per_pa["h"])

    min_bb_per_pa: float = min(per_pa["bb"])
    max_bb_per_pa: float = max(per_pa["bb"])

    min_k_per_pa: float = min(per_pa["k"])
    max_k_per_pa: float = max(per_pa["k"])

    min_ofers_per_g: float = min(per_g["ofers"])
    max_ofers_per_g: float = max(per_g["ofers"])

    for batter in batters:
        batter.h_per_pa_normalized = (batter.h_per_pa - min_h_per_pa) / (max_h_per_pa - min_h_per_pa)
        batter.bb_per_pa_normalized = 1 - (batter.bb_per_pa - min_bb_per_pa) / (max_bb_per_pa - min_bb_per_pa)
        batter.k_per_pa_normalized = 1 - (batter.k_per_pa - min_k_per_pa) / (max_k_per_pa - min_k_per_pa)
        batter.ofers_per_g_normalized = 1 - (batter.ofers_per_g - min_ofers_per_g) / (max_ofers_per_g - min_ofers_per_g)

    return batters

def process_pitchers(games: list[Game]) -> list[Pitcher]:
    # pitchers h_per_bf

    pitchers: list[Pitcher] = []
    for game in games:
        for team in game.teams:
            if team.lineup.starting_pitcher.bf:
                pitchers.append(team.lineup.starting_pitcher)

    # sort pitchers by bf
    pitchers.sort(key=lambda p: p.bf, reverse=True)

    # get the top 80% bf
    pitchers = pitchers[:int(len(pitchers) * 0.80)]
    print(f"Top 80% bf: {pitchers[-1].bf}")

    # normalize hits per bf
    per_bf: dict[str, list[float]] = {"h": [], "bb": [], "k": []}

    for pitcher in pitchers:
        per_bf["h"].append(pitcher.h_per_bf)
        per_bf["bb"].append(pitcher.bb_per_bf)
        per_bf["k"].append(pitcher.k_per_bf)

    min_h_per_bf: float = min(per_bf["h"])
    max_h_per_bf: float = max(per_bf["h"])

    min_bb_per_bf: float = min(per_bf["bb"])
    max_bb_per_bf: float = max(per_bf["bb"])

    min_k_per_bf: float = min(per_bf["k"])
    max_k_per_bf: float = max(per_bf["k"])

    for pitcher in pitchers:
        pitcher.h_per_bf_normalized = (pitcher.h_per_bf - min_h_per_bf) / (max_h_per_bf - min_h_per_bf)
        pitcher.bb_per_bf_normalized = 1 - (pitcher.bb_per_bf - min_bb_per_bf) / (max_bb_per_bf - min_bb_per_bf)
        pitcher.k_per_bf_normalized = 1 - (pitcher.k_per_bf - min_k_per_bf) / (max_k_per_bf - min_k_per_bf)

    return pitchers

def process_bullpens(games: list[Game]) -> list[Bullpen]:

    bullpens: list[Bullpen] = []

    for game in games:
        for team in game.teams:
            bullpens.append(team.lineup.bullpen)

    per_bf: dict[str, list[float]] = {"h": [], "bb": [], "k": []}

    for bullpen in bullpens:
        per_bf["h"].append(bullpen.h_per_bf)
        per_bf["bb"].append(bullpen.bb_per_bf)
        per_bf["k"].append(bullpen.k_per_bf)

    min_h_per_bf: float = min(per_bf["h"])
    max_h_per_bf: float = max(per_bf["h"])

    min_bb_per_bf: float = min(per_bf["bb"])
    max_bb_per_bf: float = max(per_bf["bb"])

    min_k_per_bf: float = min(per_bf["k"])
    max_k_per_bf: float = max(per_bf["k"])

    for bullpen in bullpens:
        bullpen.h_per_bf_normalized = (bullpen.h_per_bf - min_h_per_bf) / (max_h_per_bf - min_h_per_bf)
        bullpen.bb_per_bf_normalized = 1 - (bullpen.bb_per_bf - min_bb_per_bf) / (max_bb_per_bf - min_bb_per_bf)
        bullpen.k_per_bf_normalized = 1 - (bullpen.k_per_bf - min_k_per_bf) / (max_k_per_bf - min_k_per_bf)

    return bullpens

def process_teams(games: list[Game]) -> list[Team]:
    # team h_per_pa
    # team bb_per_pa
    # team k_per_pa
    # team totals
    # team moneyline

    teams: list[Team] = []

    for game in games:
        for team in game.teams:
            if team.odds.total and team.odds.moneyline:
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
    odds: dict[str, list[float]] = {"total": [], "moneyline": []}
    for t in teams:
        per_pa["h"].append(t.h_per_pa)
        per_pa["bb"].append(t.bb_per_pa)
        per_pa["k"].append(t.k_per_pa)

        odds["total"].append(t.odds.total)
        odds["moneyline"].append(t.odds.moneyline)

    min_h_per_pa: float = min(per_pa["h"])
    max_h_per_pa: float = max(per_pa["h"])

    min_bb_per_pa: float = min(per_pa["bb"])
    max_bb_per_pa: float = max(per_pa["bb"])

    min_k_per_pa: float = min(per_pa["k"])
    max_k_per_pa: float = max(per_pa["k"])

    min_total: float = min(odds["total"])
    max_total: float = max(odds["total"])

    min_moneyline: float = min(odds["moneyline"])
    max_moneyline: float = max(odds["moneyline"])

    for team in teams:
        team.h_per_pa_normalized = (team.h_per_pa - min_h_per_pa) / (max_h_per_pa - min_h_per_pa)
        team.bb_per_pa_normalized = (team.bb_per_pa - min_bb_per_pa) / (max_bb_per_pa - min_bb_per_pa)
        team.k_per_pa_normalized = 1 - (team.k_per_pa - min_k_per_pa) / (max_k_per_pa - min_k_per_pa)
        team.odds.total_normalized = (team.odds.total - min_total) / (max_total - min_total)
        team.odds.implied_normalized = (team.odds.implied - min_moneyline) / (max_moneyline - min_moneyline)

    return teams

def evaluate_batters(games: list[Game]) -> list[Batter]:

    evaluated_batters: list[Batter] = []

    for game in games:
        for i, team in enumerate(game.teams):
            for batter in team.lineup.batters:
                if (
                    batter.order <= 6 and
                    batter.h_per_pa_normalized and 
                    game.teams[i - 1].lineup.starting_pitcher.h_per_bf_normalized and
                    team.h_per_pa_normalized # and 
                    # team.odds.total_normalized and 
                    # team.odds.implied_normalized
                ):
                    batter.evaluate = {
                        # sum of the weights should be equal to the number of weights so the evaluation is 0-1
                        "ofers_per_game": (batter.ofers_per_g_normalized) * 1.5,
                        "h_per_pa": (batter.h_per_pa_normalized) * 1.25,
                        "bb_per_pa": (batter.bb_per_pa_normalized) * 1.125,
                        "k_per_pa": (batter.k_per_pa_normalized) * 1.125,

                        "sp_h_per_bf": (game.teams[i - 1].lineup.starting_pitcher.h_per_bf_normalized) * 1.25,
                        "sp_bb_per_bf": (game.teams[i - 1].lineup.starting_pitcher.bb_per_bf_normalized) * 1.125,
                        "sp_k_per_bf": (game.teams[i - 1].lineup.starting_pitcher.k_per_bf_normalized) * 1.125,

                        "bp_h_per_pa": (game.teams[i-1].lineup.bullpen.h_per_bf_normalized) * 0.875,
                        "bp_bb_per_pa": (game.teams[i-1].lineup.bullpen.bb_per_bf_normalized) * 0.8125,
                        "bp_k_per_pa": (game.teams[i-1].lineup.bullpen.k_per_bf_normalized) * 0.8125,

                        "team_h_per_pa": (team.h_per_pa_normalized) * 0.5,
                        # "team_bb_per_pa": (team.bb_per_pa_normalized) * 0.666,
                        "team_k_per_pa": (team.k_per_pa_normalized) * 0.5,

                        # "total": (team.odds.total_normalized) * 1.0,
                        # "implied": (team.odds.implied_normalized) * 0.5
                    }
                    batter.evaluation = statistics.mean(list(batter.evaluate.values()))
                    evaluated_batters.append(batter)

    return evaluated_batters

def dump(evaluated_batters: list[Batter], batters: list[Batter], pitchers: list[Pitcher], bullpens: list[Bullpen], teams: list[Team]):

    # batters
    evaluated_batters.sort(key=lambda b: -b.evaluation)
    json.dump(evaluated_batters, open("evaluations/evaluation.json", "w"), indent=4, default=lambda o: o.__dict__)

    batters.sort(key=lambda b: -b.h_per_pa_normalized)
    json.dump(batters, open("evaluations/batters_h_per_pa.json", "w"), indent=4, default=lambda o: o.__dict__)

    batters.sort(key=lambda b: -b.bb_per_pa_normalized)
    json.dump(batters, open("evaluations/batters_bb_per_pa.json", "w"), indent=4, default=lambda o: o.__dict__)

    batters.sort(key=lambda b: -b.k_per_pa_normalized)
    json.dump(batters, open("evaluations/batters_k_per_pa.json", "w"), indent=4, default=lambda o: o.__dict__)

    # pitchers
    pitchers.sort(key=lambda p: -p.h_per_bf_normalized)
    json.dump(pitchers, open("evaluations/pitchers_h_per_bf.json", "w"), indent=4, default=lambda o: o.__dict__)

    pitchers.sort(key=lambda p: -p.bb_per_bf_normalized)
    json.dump(pitchers, open("evaluations/pitchers_bb_per_bf.json", "w"), indent=4, default=lambda o: o.__dict__)

    pitchers.sort(key=lambda p: -p.k_per_bf_normalized)
    json.dump(pitchers, open("evaluations/pitchers_k_per_bf.json", "w"), indent=4, default=lambda o: o.__dict__)

    # bullpens
    bullpens.sort(key=lambda b: -b.h_per_bf_normalized)
    json.dump(bullpens, open("evaluations/bullpens_h_per_bf.json", "w"), indent=4, default=lambda o: o.__dict__)

    bullpens.sort(key=lambda b: -b.k_per_bf_normalized)
    json.dump(bullpens, open("evaluations/bullpens_k_per_bf.json", "w"), indent=4, default=lambda o: o.__dict__)

    # teams
    teams.sort(key=lambda t: -t.h_per_pa_normalized)
    json.dump(teams, open("evaluations/teams_batters_h_per_pa.json", "w"), indent=4, default=lambda o: o.__dict__)

    teams.sort(key=lambda t: -t.bb_per_pa_normalized)
    json.dump(teams, open("evaluations/teams_batters_bb_per_pa.json", "w"), indent=4, default=lambda o: o.__dict__)

    teams.sort(key=lambda t: -t.k_per_pa_normalized)
    json.dump(teams, open("evaluations/teams_batters_k_per_pa.json", "w"), indent=4, default=lambda o: o.__dict__)

    teams.sort(key=lambda t: -t.h_per_pa_normalized)
    json.dump(teams, open("evaluations/teams_total_h_per_pa.json", "w"), indent=4, default=lambda o: o.__dict__)

    teams.sort(key=lambda t: -t.bb_per_pa_normalized)
    json.dump(teams, open("evaluations/teams_total_bb_per_pa.json", "w"), indent=4, default=lambda o: o.__dict__)

def main(args):

    if args[0] == "games":

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        browser = webdriver.Chrome(options=options, executable_path="chromedrivers/chromedriver100")

        try:
            
            d: datetime = datetime.now() + timedelta(days=0)
            date_string = d.strftime("%Y%m%d")
            print(f"Date: {d.strftime('%B %d, %Y')}")

            games: list[Game] = get_games(browser, date_string)

            for game in games:
                game.get_game_details(browser)

            pickle.dump(games, open("games.pkl", "wb"))
            json.dump(games, open(f"games/games_{date_string}.json", "w"), indent=4, default=lambda o: o.__dict__)
            print("\nDumped games...")
        
        except Exception as e:
            print(traceback.format_exc())

        browser.close()

        args[0] = "stats"

    if args[0] == "stats":
        games: list[Game] = pickle.load(open(f"games.pkl", "rb"))

        batters: list[Batter] = process_batters(games)
        pitchers: list[Pitcher] = process_pitchers(games)
        bullpens: list[Bullpen] = process_bullpens(games)
        teams: list[Team] = process_teams(games)

        evaluated_batters: list[Batter] = evaluate_batters(games)
    
        evaluated_batters.sort(key=lambda b: -b.evaluation)
        print(f"\n# Player\tTeam\tEval\tPA\tG\tOPG\tH/PA\tBB/PA\tK/PA")
        for batter in evaluated_batters:
            if batter.evaluation >= 0.7:
                print(f"{batter.order} {batter.name.split(' ')[1]}\t{batter.team_abbreviation}\t{batter.evaluation:.3f}\t{batter.pa}\t{batter.g}\t{batter.ofers_per_g:.3f}\t{batter.h_per_pa:.3f}\t{batter.bb_per_pa:.3f}\t{batter.k_per_pa:.3f}")
        dump(evaluated_batters, batters, pitchers, bullpens, teams)

if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)