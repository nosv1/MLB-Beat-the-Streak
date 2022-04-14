import json

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By

url = "https://api.actionnetwork.com/web/v1/games/122419"

# get the url using Chrome headless
options = webdriver.ChromeOptions()
options.add_argument('headless')
browser = webdriver.Chrome(options=options)
browser.get(url)

# get the json from browser
# Please use find_element(by=By.TAG_NAME, value=name) instead
json_data = json.loads(browser.find_element_by_tag_name('body').text)
json.dump(json_data, open("tgame.json", "w"), indent=4)

# close browser
browser.close()

# solve selenium has no attribute 'webdriver'