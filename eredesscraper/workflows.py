# package imports
from pathlib import Path

import typer

from eredesscraper.agent import EredesScraper
from eredesscraper.db_clients import InfluxDB
from eredesscraper.utils import parse_config


def switchboard(name: str, db: str, config_path: Path, month: int, delta:bool = False) -> None:
    """
    The run function is the entry point.

    :param name: str: Specify which workflow to run. One of: ``current_month``
    :type name: str
    :param db: str: Specify which database to use. One of: ``influxdb``
    :type db: str
    :param config_path: Path: Specify the path to the config file
    :type config_path: pathlib.Path
    :return: None
    :doc-author: Ricardo Filipe dos Santos
    """

    config = parse_config(config_path=config_path)

    typer.echo(f"🚀\tRunning {typer.style(name, fg=typer.colors.GREEN)} workflow")

    typer.echo(f"📇\tE-REDES client info: "
               f"NIF: {typer.style(config['eredes']['nif'], fg=typer.colors.GREEN, bold=True)}, "
               f"CPE: {typer.style(config['eredes']['cpe'], fg=typer.colors.GREEN, bold=True)}")

    match name:
        case 'current_month':
            bot = EredesScraper(
                nif=config['eredes']['nif'],
                password=config['eredes']['pwd'],
                cpe_code=config['eredes']['cpe']
            )
            bot.setup()
            bot.current_month()
            bot.teardown()

        case 'last_month':
            bot = EredesScraper(
                nif=config['eredes']['nif'],
                password=config['eredes']['pwd'],
                cpe_code=config['eredes']['cpe']
            )
            bot.setup()
            bot.last_month()
            bot.teardown()

        case 'select_month':
            bot = EredesScraper(
                nif=config['eredes']['nif'],
                password=config['eredes']['pwd'],
                cpe_code=config['eredes']['cpe']
            )
            bot.setup()
            bot.select_month(month=month)
            bot.teardown()

        case _:
            typer.echo(f"??\tWorkflow {typer.style(name, fg=typer.colors.GREEN)} not supported")
            raise typer.Exit(code=1)

    match db:
        case 'influxdb':
            db = InfluxDB(
                token=config['influxdb']['token'],
                org=config['influxdb']['org'],
                host=config['influxdb']['host'],
                port=config['influxdb']['port'],
                bucket=config['influxdb']['bucket'])
            db.connect()
            db.load(source_data=bot.dwnl_file, cpe_code=config['eredes']['cpe'], delta=delta)

        case '':
            pass

        case _:
            typer.echo(f"??\tDatabase {typer.style(db, fg=typer.colors.GREEN)} not supported")