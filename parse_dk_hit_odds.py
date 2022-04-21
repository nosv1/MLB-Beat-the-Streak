import json
import traceback

from dataclasses import dataclass
from selenium import webdriver

class DK_Batters_Scoring:
    points: dict = {
        "Singles": 3,
        "Doubles": 5,
        "Triples": 8,
        "Home Runs": 10,
        "RBIs": 2,
        "Runs Scored": 2,
        "Walks": 2,  # no props for
        "Hit By Pitch": 2,  # no props for
        "Stolen Bases": 5
    }
    points["Home Runs"] = points["Home Runs"] + points["RBIs"] + points["Runs Scored"]

class Odds:
    def __init__(self, label: str, odds: int = None, line: float = None) -> None:
        self.label: str = label  # over/under
        self.odds: int = odds  # -145, +105, etc
        self.line: float = line  # 0.5, 1.5, etc

        if self.odds and self.line:
            self.implied_odds: float = self.get_implied_odds(odds)
            self.implied_outcome: float = self.get_implied_outcome(self.line, self.implied_odds)

    def get_implied_outcome(self, line: float, implied_odds: float) -> float:
        if self.label == "Over":
            return implied_odds * line
        else:
            return implied_odds * (line / 2)

    def get_implied_odds(self, odds: int) -> float:
        if odds < 0:
            return (-1 * odds) / (-1 * odds + 100)
        else: 
            return 100 / (odds + 100)

class Prop:
    def __init__(self, name: str) -> None:
        self.name = name
        self.odds: list[Odds] = []
        self.points: float = None

    def get_average_odds(self) -> Odds:
        odds = Odds(
            label="Average"
        )
        odds.implied_outcome = sum([x.implied_outcome for x in self.odds]) / len(self.odds)
        return odds

    def calculate_points(self) -> None:
        self.points = self.odds[-1].implied_outcome * DK_Batters_Scoring.points[self.name]

class Batter:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.props: dict[str, Prop] = {}
        self.total_points: float = None

    def calculate_singles_prop(self, singles_prop: Prop) -> Prop:
        singles_prop.odds.append(
            Odds(label="Average")
        )
        singles_prop.odds[-1].implied_outcome = (
            self.props["Hits"].odds[-1].implied_outcome - 
            self.props["Doubles"].odds[-1].implied_outcome if "Doubles" in self.props else 0 -
            self.props["Triples"].odds[-1].implied_outcome if "Triples" in self.props else 0 -
            self.props["Home Runs"].odds[-1].implied_outcome if "Home Runs" in self.props else 0
        )
        return singles_prop


def get_odds(browser: webdriver.Chrome):
    
    # Batter Props
    url = "https://sportsbook-us-il.draftkings.com/sites/US-IL-SB/api/v4/eventgroups/88670847/categories/743/"
    browser.get(url)
    json_data = json.loads(browser.find_element_by_tag_name("body").text)

    batters: dict[str, Batter] = {}
    for i, offer_category_json in enumerate(json_data["eventGroup"]["offerCategories"]):
        if offer_category_json["name"] == "Batter Props":

            for j, offer_subcategory_descriptor_json in enumerate(offer_category_json["offerSubcategoryDescriptors"]):

                subcategory_url = url + f"subcategories/{offer_subcategory_descriptor_json['subcategoryId']}"
                browser.get(subcategory_url)
                subcateogry_json = json.loads(browser.find_element_by_tag_name("body").text)
                json.dump(
                    subcateogry_json, 
                    open(f"dk_odds/{offer_subcategory_descriptor_json['name']}.json", "w"), 
                    indent=4, 
                    default=lambda o: o.__dict__
                )
                print(f"Getting {offer_subcategory_descriptor_json['name']}...")

                for offers_json in subcateogry_json["eventGroup"]["offerCategories"][i]["offerSubcategoryDescriptors"][j]["offerSubcategory"]["offers"]:
                    

                    for offer_json in offers_json:
                        
                        batter: Batter = None
                        prop = Prop(offer_subcategory_descriptor_json["name"])
                        for outcome_json in offer_json["outcomes"]:

                            if "participant" in outcome_json:
                                name = outcome_json["participant"]
                                if name in batters:
                                    batter = batters[name]
                                else:
                                    batters[name] = Batter(name)
                                    batter = batters[name]

                                if prop.name not in batter.props:
                                    batter.props[prop.name] = prop

                                batter.props[prop.name].odds.append(
                                    Odds(
                                        label=outcome_json["label"],
                                        odds=int(outcome_json["oddsAmerican"]),
                                        line=outcome_json["line"]
                                    )
                                )
                        
                        # get the average of the odds
                        if batter:
                            batter.props[prop.name].odds.append(
                                batter.props[prop.name].get_average_odds()
                            )
                            batters[batter.name] = batter

            for batter_name, batter in batters.items():
                batter.props["Singles"] = Prop("Singles")
                batter.props["Singles"] = batter.calculate_singles_prop(batter.props["Singles"])

                for name, prop in batter.props.items():
                    if name in DK_Batters_Scoring.points:
                        batter.props[name].calculate_points()

                batter.total_points = sum([x.points for x in batter.props.values() if x.points])
            break

    return batters

def main():

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    browser = webdriver.Chrome(options=options, executable_path="chromedrivers/chromedriver100")

    try:
        batters: dict[str, Batter] = get_odds(browser)
        batters = {k: v for k, v in sorted(batters.items(), key=lambda item: item[1].total_points, reverse=True)}
        json.dump(batters, open("dk_batters.json", "w"), indent=4, default=lambda o: o.__dict__)

    except:
        print(traceback.format_exc())

    browser.close()

if __name__ == "__main__":
    main()