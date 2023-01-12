from time import sleep
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os

from eredes_agent import EredesDriver

bot = EredesDriver()

bot.headless = False

bot.driver.get(bot.config['EREDES_CONSUMPTION_STREAM_URL'])

sleep(20)

bot.login_private_user()

bot.driver.quit()