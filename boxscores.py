import json
import os
import traceback

from datetime import datetime, timedelta
from selenium import webdriver

def get_boxscore(game_id: str, browser: webdriver.Chrome):
    url: str = f"https://api.foxsports.com/bifrost/v1/mlb/event/{game_id}/data?apikey=jE7yBJVRNAwdDesMgTzTXUUSx1It41Fq"
    browser.get(url)
    try:
        boxscore_json = json.loads(browser.find_element_by_tag_name("body").text)["boxscore"]["boxscoreSections"]
    except KeyError:
        return 

    return boxscore_json

def get_games(date_string: str, browser: webdriver.Chrome):

    url: str = f"https://api.foxsports.com/bifrost/v1/mlb/scoreboard/segment/{date_string}?apikey=jE7yBJVRNAwdDesMgTzTXUUSx1It41Fq"
    browser.get(url)
    day_json = json.loads(browser.find_element_by_tag_name("body").text)

    for game_json in day_json["sectionList"][0]["events"]:
        game_id: str = game_json["entityLink"]["layout"]["tokens"]["id"]
        print(f"Date: {date_string} Game: {game_id}", end="")

        boxscore_json = get_boxscore(game_id, browser)    
        if boxscore_json:
            json.dump(boxscore_json, open(f"boxscores/{date_string}/{game_id}.json", "w"), indent=4)
            
        print(f" {'✓' if boxscore_json else '✗'}")

def main():

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    browser = webdriver.Chrome(options=options, executable_path="chromedrivers/chromedriver100")

    try:
        # d: datetime = datetime(2021, 4, 1)
        # while d < datetime(2022, 1, 1):
            # for i in range(7, 14):
            # date_string = datetime(2022, 4, i).strftime("%Y%m%d")
        d: datetime = datetime.now() + timedelta(days=-1)
        date_string = d.strftime("%Y%m%d")
        
        if not os.path.exists(f"boxscores/{date_string}"):
            os.makedirs(f"boxscores/{date_string}")

        get_games(date_string, browser)
        d += timedelta(days=1)

    except:
        print(traceback.format_exc())

    browser.close()

if __name__ == '__main__':
    main()