# package imports
from pathlib import Path

import typer

from eredesscraper.agent import EredesScraper
from eredesscraper.db_clients import InfluxDB
from eredesscraper.utils import parse_config


def switchboard(name: str, db: str, config_path: Path) -> None:
    """
    The run function is the entry point.

    :param name: str: Specify which workflow to run. One of: ``current_month_consumption``
    :type name: str
    :param db: str: Specify which database to use. One of: ``influxdb``
    :type db: str
    :param config_path: Path: Specify the path to the config file
    :type config_path: pathlib.Path
    :return: None
    :doc-author: Ricardo Filipe dos Santos
    """

    config = parse_config(config_path=config_path)

    match name:
        case 'current_month_consumption':
            typer.echo(f"🚀\tRunning {typer.style('current_month_consumption', fg=typer.colors.GREEN)} workflow")

            typer.echo(f"📇\tE-REDES client info: "
                       f"NIF: {typer.style(config['eredes']['nif'], fg=typer.colors.GREEN, bold=True)}, "
                       f"CPE: {typer.style(config['eredes']['cpe'], fg=typer.colors.GREEN, bold=True)}")

            bot = EredesScraper(
                nif=config['eredes']['nif'],
                password=config['eredes']['pwd'],
                cpe_code=config['eredes']['cpe']
            )
            bot.setup()
            bot.current_month_consumption()
            bot.teardown()

        case _:
            typer.echo(f"??\tWorkflow {typer.style(name, fg=typer.colors.GREEN)} not supported")

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

        case '':
            pass

        case _:
            typer.echo(f"??\tDatabase {typer.style(db, fg=typer.colors.GREEN)} not supported")