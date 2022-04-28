from copyreg import pickle
from datetime import datetime
import json
import pickle
import traceback

from selenium import webdriver

from dk_classes import DK_Batters_Scoring, Odds, Prop, Batter, Event

def get_odds(browser: webdriver.Chrome):
    
    # Batter Props
    # https://sportsbook.draftkings.com/leagues/baseball/88670847?category=batter-props
    url = "https://sportsbook-us-il.draftkings.com/sites/US-IL-SB/api/v4/eventgroups/88670847/categories/743/"
    browser.get(url)
    json_data = json.loads(browser.find_element_by_tag_name("body").text)

    for i, event in enumerate(json_data["eventGroup"]["events"]):
        event = Event(
            id=event["providerEventId"],
            name=event["name"],
            start_date=datetime.strptime(event["startDate"].split(".")[0], "%Y-%m-%dT%H:%M:%S")
        )
        print(event.to_string())
    print(f"Games: {i+1}")
    print()

    batters: dict[str, Batter] = {}
    for i, offer_category_json in enumerate(json_data["eventGroup"]["offerCategories"]):
        offer_category_name = offer_category_json["name"]
        if offer_category_name == "Batter Props":

            for j, offer_subcategory_descriptor_json in enumerate(offer_category_json["offerSubcategoryDescriptors"]):
                offer_subcategory_descriptor_name = offer_subcategory_descriptor_json["name"]

                if offer_subcategory_descriptor_name in DK_Batters_Scoring.points:

                    tries = 3
                    while tries > 0:
                        tries -= 1
                        try:
                            subcategory_url = url + f"subcategories/{offer_subcategory_descriptor_json['subcategoryId']}"
                            browser.get(subcategory_url)
                            subcateogry_json = json.loads(browser.find_element_by_tag_name("body").text)
                            json.dump(
                                subcateogry_json, 
                                open(f"draft_kings/dk_odds/{offer_subcategory_descriptor_name}.json", "w"), 
                                indent=4, 
                                default=lambda o: o.__dict__
                            )
                            print(f"Getting {offer_subcategory_descriptor_name}...")
                            print(f"{url}")

                            for offers_json in subcateogry_json["eventGroup"]["offerCategories"][i]["offerSubcategoryDescriptors"][j]["offerSubcategory"]["offers"]:
                                
                                for offer_json in offers_json:
                                    
                                    batter: Batter = None
                                    prop = Prop(offer_subcategory_descriptor_json["name"])
                                    provider_event_id = offer_json["providerEventId"]
                                    key = None
                                    for outcome_json in offer_json["outcomes"]:

                                        if "participant" in outcome_json:
                                            name = outcome_json["participant"]
                                            key = f"{name} ({provider_event_id})"
                                            if key in batters:
                                                batter = batters[key]
                                            else:
                                                batters[key] = Batter(name)
                                                batter = batters[key]

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
                                        batters[key] = batter

                            break
                        except KeyError:
                            print(f"KeyError, Tries left: {tries}")

                if batters.items():
                    for batter_name, batter in batters.items():
                        for name, prop in batter.props.items():
                            if name in DK_Batters_Scoring.points:
                                batter.props[name].calculate_points()

                        batter.total_points = sum([x.points for x in batter.props.values() if x.points])
                
                else:
                    print(f"No batter props found for {offer_subcategory_descriptor_name}")
                    
            break

    return batters

def main():

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    browser = webdriver.Chrome(options=options, executable_path="chromedrivers/chromedriver100")

    try:
        batters: dict[str, Batter] = get_odds(browser)

        batters = {k: v for k, v in sorted(batters.items(), key=lambda item: item[1].total_points, reverse=True)}
        json.dump(batters, open("draft_kings/dk_batters.json", "w"), indent=4, default=lambda o: o.__dict__)
        pickle.dump(batters, open("pickles/dk_batters.pkl", "wb"))

        # sort based on hits
        batters = {k: v for k, v in batters.items() if "Hits" in v.props}
        batters = {k: v for k, v in sorted(batters.items(), key=lambda item: item[1].props["Hits"].odds[-1].implied_outcome, reverse=True)}
        json.dump(batters, open("draft_kings/dk_batters_hits.json", "w"), indent=4, default=lambda o: o.__dict__)

    except:
        print(traceback.format_exc())

    browser.close()

if __name__ == "__main__":
    main()