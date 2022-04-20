import json
import traceback

from dataclasses import dataclass
from selenium import webdriver

class Odds:
    def __init__(self, label: str, odds: int, line: float) -> None:
        self.label: str = label  # over/under
        self.odds: int = odds  # -145, +105, etc
        self.line: float = line  # 0.5, 1.5, etc

        self.implied_odds: float = self.get_implied_odds(odds)
        self.implied_hits: float = self.get_implied_hits(self.line, self.implied_odds)

    def get_implied_hits(self, line: float, implied_odds: float) -> float:
        if self.label == "Over":
            return implied_odds * line
        else:
            return implied_odds * (line / 2)

    def get_implied_odds(self, odds: int) -> float:
        if odds < 0:
            return (-1 * odds) / (-1 * odds + 100)
        else: 
            return 100 / (odds + 100)

class Batter:
    def __init__(self, name: str, odds: Odds) -> None:
        self.name: str = name
        self.odds: Odds = odds


def get_odds(browser: webdriver.Chrome):
    
    url = "https://sportsbook-us-il.draftkings.com//sites/US-IL-SB/api/v4/eventgroups/88670847/categories/743/subcategories/6719?format=json"
    browser.get(url)
    json_data = json.loads(browser.find_element_by_tag_name("body").text)

    batters: list [Batter] = []
    for offer_category_json in json_data["eventGroup"]["offerCategories"]:
        if offer_category_json["name"] == "Batter Props":

            for offer_subcategory_descriptor_json in offer_category_json["offerSubcategoryDescriptors"]:
                if offer_subcategory_descriptor_json["name"] == "Hits":

                    for offers_json in offer_subcategory_descriptor_json["offerSubcategory"]["offers"]:
                        
                        for offer_json in offers_json:

                            for outcome_json in offer_json["outcomes"]:

                                if "participant" in outcome_json:
                                    batters.append(
                                        Batter(
                                            name=outcome_json["participant"],
                                            odds=Odds(
                                                label=outcome_json["label"],
                                                odds=int(outcome_json["oddsAmerican"]),
                                                line=float(outcome_json["line"])
                                            )
                                        )
                                    )
                    break
            break

    return batters

def main():

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    browser = webdriver.Chrome(options=options, executable_path="chromedrivers/chromedriver100")

    try:
        batters: list[Batter] = get_odds(browser)
        batters.sort(key=lambda b: -b.odds.implied_hits)
        json.dump(batters, open("dk_batters.json", "w"), indent=4, default=lambda o: o.__dict__)

    except:
        print(traceback.format_exc())

    browser.close()

if __name__ == "__main__":
    main()