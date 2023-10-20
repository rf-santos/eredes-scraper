# package imports
from eredes_scraper import EredesScraper
from utils import parse_config
from pathlib import Path
from db_clients import InfluxDB

config = parse_config()      # specify the path to the config.yml file if different from default

bot = EredesScraper()
bot.setup()
bot.current_month_consumption()
bot.teardown()

db = InfluxDB()
db.connect()
db.load(source_data=bot.dwnl_file)