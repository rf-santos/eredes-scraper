# package imports
from agent import EredesScraper
from utils import parse_config
from pathlib import Path
from db_clients import InfluxDB


def run(workflow: str, config_path: Path):
    match workflow:
        case 'current_month_consumption':
            print("Running current_month_consumption workflow")
            print(f"Using config file: {config_path}")

            config = parse_config(config_path=config_path)  # specify the path to the config.yml file if different from default

            print(f"E-Redes client info: NIF: {config['eredes']['nif']}, CPE: {config['eredes']['cpe']}")

            bot = EredesScraper()
            bot.setup()
            bot.current_month_consumption()
            bot.teardown()

            db = InfluxDB(
                token=config['influxdb']['token'],
                org=config['influxdb']['org'],
                host=config['influxdb']['host'],
                port=config['influxdb']['port'],
                bucket=config['influxdb']['bucket'])
            db.connect()
            db.load(source_data=bot.dwnl_file, cpe_code=config['eredes']['cpe'])
