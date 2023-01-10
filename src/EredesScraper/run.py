from time import sleep

from eredes_agent import EredesDriver

bot = EredesDriver()

bot.driver.get(bot.config['EREDES_CONSUMPTION_STREAM_URL'])

sleep(20)

bot.login_private_user()

bot.driver.quit()