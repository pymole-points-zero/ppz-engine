from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
driver.get("http://eidokropki.reaktywni.pl/games-adv.phtml?a=&b=&arank0=&arank1=&brank0=&brank1=&tourn=all&board%5B3932%5D=3932&result%5BA%5D=A&result%5BB%5D=B&rules%5BN%5D=N&page=82")
start_cut = 110	# if bug apears at half of page then cut n previous games
# loop
while True:
	# a tag to game pages of current advanced search page

	WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'html')))

	cur_games_links = driver.find_elements_by_xpath("//tbody//tr/td[1]/a")
	if start_cut is not None:
		cur_games_links = cur_games_links[start_cut:]
		start_cut = None

	for a in cur_games_links:
		handles_before = driver.window_handles

		# new game tab
		a.send_keys(Keys.CONTROL + Keys.SHIFT + Keys.RETURN)

		WebDriverWait(driver, 10).until(
			lambda driver: len(handles_before) != len(driver.window_handles))

		driver.switch_to.window(driver.window_handles[1])

		# download game
		download_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, 'Загрузить SGF')))
		
		# scroll to button
		driver.execute_script("arguments[0].scrollIntoView(true);", download_button)

		# check if clickable
		WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, 'Загрузить SGF')))

		download_button.click()

		# close game tab
		driver.close()
		driver.switch_to.window(driver.window_handles[0])

	# next page link
	nav_links = driver.find_elements_by_xpath("//table[@class='games']/following-sibling::p/a")

	# if there is no next page then stop
	if not nav_links:
		break

	last_link = nav_links[-1]

	if last_link.text != ">>>":
		break

	last_link.click()