from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from engine import Game
import time
import os

download_dir = r'C:\Users\Roman\Downloads\data'
drive_dir = r'C:\Users\Roman\Desktop\Проекты\Курсач 2018\scraping\geckodriver.exe'


# To prevent download dialog
profile = webdriver.FirefoxProfile()
profile.set_preference('browser.download.folderList', 2) # custom location
profile.set_preference('browser.download.manager.showWhenStarting', False)
profile.set_preference('browser.download.dir', download_dir)
profile.set_preference("browser.helperApps.neverAsk.saveToDisk","application/x-go-sgf")



driver = webdriver.Firefox(firefox_profile=profile, executable_path=drive_dir)

# go to advanced search page
driver.get("http://eidokropki.reaktywni.pl/games-adv.phtml?a=&b=&arank0=1400&arank1=&brank0=1400&brank1=&result%5BA%5D=A&result%5BB%5D=B&rules%5BN%5D=N&board%5B3932%5D=3932&tourn=all&lang=en")

# loop
while True:
	# a tag to game pages of current advanced search page

	cur_games_links = driver.find_elements_by_xpath("//tbody//tr/td[1]/a")

	for a in cur_games_links:
		# new game tab
		a.send_keys(Keys.CONTROL + Keys.SHIFT + Keys.RETURN)

		time.sleep(2)
		driver.switch_to.window(driver.window_handles[1])

		# download game
		download_button = driver.find_element_by_link_text('Download SGF')
		download_button.click()

		# close game tab
		driver.close()

	# next page link
	nav_links = driver.find_elements_by_xpath("//table[@class='games']/following-sibling::p/a")

	# if there is no next page then stop
	if not nav_links:
		break

	last_link = nav_links[-1]

	if last_link.text != ">>>":
		break

	last_link.click()
	time.sleep(5)