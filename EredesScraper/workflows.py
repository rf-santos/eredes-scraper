# package imports
from pathlib import Path

from EredesScraper.agent import EredesScraper
from EredesScraper.utils import parse_config
from EredesScraper.db_clients import InfluxDB


def run(workflow: str, db: str, config_path: Path) -> None:
    """
    The run function is the entry point.

    :param workflow: str: Specify which workflow to run. One of: ``current_month_consumption``
    :type workflow: str
    :param db: str: Specify which database to use. One of: ``influxdb``
    :type db: str
    :param config_path: Path: Specify the path to the config file
    :type config_path: pathlib.Path
    :return: None
    :doc-author: Ricardo Filipe dos Santos
    """

    config = parse_config(config_path=config_path)

    match workflow:
        case 'current_month_consumption':
            print("Running current_month_consumption workflow")
            print(f"Using config file: {config_path}")

            print(f"E-Redes client info: NIF: {config['eredes']['nif']}, CPE: {config['eredes']['cpe']}")

            bot = EredesScraper(
                nif=config['eredes']['nif'],
                password=config['eredes']['pwd'],
                cpe_code=config['eredes']['cpe']
            )
            bot.setup()
            bot.current_month_consumption()
            bot.teardown()
            print(f"Downloaded file: {bot.dwnl_file}")

    match db:
        case 'influxdb':
            db = InfluxDB(
                token=config['influxdb']['token'],
                org=config['influxdb']['org'],
                host=config['influxdb']['host'],
                port=config['influxdb']['port'],
                bucket=config['influxdb']['bucket'])
            db.connect()
            db.load(source_data=bot.dwnl_file, cpe_code=config['eredes']['cpe'])