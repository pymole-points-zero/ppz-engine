from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from engine import Game
import time
import os


# -------------------------

download_dir = r'C:\Users\Roman\Downloads\data'
firefox_drive_dir = r'C:\Users\Roman\Desktop\Проекты\Курсач 2018\scraping\geckodriver.exe'
chrome_drive_dir = r'C:\Users\Roman\Desktop\Проекты\Курсач 2018\scraping\chromedriver.exe'

'''
# To prevent download dialog
profile = webdriver.FirefoxProfile()
profile.set_preference('browser.download.folderList', 2) # custom location
profile.set_preference('browser.download.manager.showWhenStarting', False)
profile.set_preference('browser.download.dir', download_dir)
profile.set_preference("browser.helperApps.neverAsk.saveToDisk","application/x-go-sgf")

driver = webdriver.Firefox(firefox_profile=profile, executable_path=firefox_drive_dir)
'''

options = webdriver.ChromeOptions()
options.add_argument("download.default_directory=" + download_dir)
options.binary_location = "C:/Program Files (x86)/Google/Chrome Beta/Application/chrome.exe"

driver = webdriver.Chrome(chrome_drive_dir, chrome_options=options)
driver.maximize_window()

actions = ActionChains(driver)


# ------------------------

driver.get("https://vk.com/feed")

# login and password
login = driver.find_element_by_id("email").send_keys("89829853933")
password = driver.find_element_by_id("pass").send_keys("28cnfywbjyyfz2622")

submit = driver.find_element_by_id("login_button").click()

time.sleep(3)

driver.get("https://vk.com/app4214777_46337854")



# after load of app switch frame to app frame
driver.switch_to.frame(driver.find_element_by_id('fXD'))

# games
games = driver.find_element_by_link_text('Игры')
driver.execute_script("arguments[0].click();", games)

# settings for search
settings = driver.find_element_by_link_text("Фильтровать игры")
driver.execute_script("arguments[0].click();", settings)
time.sleep(1)

# sorting = driver.find_element_by_xpath("//div[@class='f-header']/form")
# sorting = driver.find_element_by_id("archive_sort")
sorting = WebDriverWait(driver, 10).until(EC.presence_of_element_located((BY.ID, "archive_sort")))
actions.move_to_element(sorting).perform()
driver.execute_script("arguments[0].click();", sorting)

time.sleep(1)

# sort by rating
rating = sorting.find_elements_by_xpath("/div/div[@class='jq-selectbox_dropdown']/ul//li")
for i in rating:
	print("По рейтингу")
	if i.text == "По рейтингу":
		rating = i
		break

time.sleep(1)
rating.click()

field = driver.find_element_by_link_text("39x32")
field.click()

ter = driver.find_element_by_link_text("Без территории, с заземлением")
ter.click()
ter = driver.find_element_by_link_text("Без территории, без заземлением")
ter.click()

ьщву = driver.find_element_by_link_text("Без доп. режима")
ter.click()

ter = driver.find_element_by_link_text("Блиц")
ter.click()

ter = driver.find_element_by_link_text("Применить и закрыть")
ter.click()

time.sleep(5)

# link inside nav panel
page_n = 1

# loop
while True:
	# a tag to game pages of current advanced search page

	cur_games_links = driver.find_elements_by_xpath('//tbody//tr')

	for a in cur_games_links:
		# go to game
		actions.move_to_element(a).perform()
		a.click()

		time.sleep(2)

		# open info
		info = driver.find_element_by_xpath('//div[@class="score-box"]//div/a')
		info.click()

		time.sleep(1)

		# save file
		save = driver.find_element_by_id("Сохранить в формате SGF")
		save.click()

		time.sleep(3)

		# go back to games
		games.click()
	

	# change page 
	page_n += 1
	try:
		page = driver.find_elements_by_link_name(str(page_n))
	except:
		break

	page.click()
	time.sleep(5)