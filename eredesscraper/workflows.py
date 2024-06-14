# package imports
import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import typer

from eredesscraper.agent import EredesScraper
from eredesscraper.db_clients import InfluxDB
from eredesscraper.utils import parse_config, flatten_config
from eredesscraper.models import ERSSession
from eredesscraper.logger import logger

user_config_path = Path().home() / ".ers"
Path.mkdir(user_config_path, exist_ok=True)

date = datetime.now()


def switchboard(config_path: Path, name: str, db: None | list = None, month: int = date.month, year: int = date.year,
                delta: bool = False, keep: bool = False, quiet: bool = False, output: Path = Path.home() / ".ers",
                uuid: uuid4 = uuid4(), headless: bool = True, debug: bool = False) -> ERSSession:
    """
    The run function is the entry point.

    :param name: str: Specify which workflow to run.
    :type name: str
    :param db: list: Specify the list of database connections to use.`
    :type db: list
    :param config_path: Path: Specify the path to the config file
    :type config_path: pathlib.Path
    :param month: int: Specify the month to load (1-12).
    :type month: int
    :param year: int: Specify the year to load (YYYY).
    :type year: int
    :param delta: bool: Specify if the data should be loaded as a delta. [Optional]
    :type delta: bool
    :param keep: bool: Specify if the source data file should be kept after loading. [Optional]
    :type keep: bool
    :param quiet: bool: Specify if the function should run in quiet mode. [Optional]
    :type quiet: bool
    :param output: Path: Specify the path to write the source data file. [Optional]
    :type output: pathlib.Path
    :param uuid: uuid4: Specify the UUID for the session. [Optional]
    :type uuid: uuid4
    :return: ERSSession: The result object of the workflow run.
    :doc-author: Ricardo Filipe dos Santos

    Args:
        headless:
    """

    date = datetime.now()

    output = output if output else Path.home() / ".ers"

    if name not in ['current', 'previous', 'select']:
        if not quiet:
            typer.echo(f"??\tWorkflow {typer.style(name, fg=typer.colors.GREEN)} not supported")
        raise typer.Exit(code=1)

    if name == 'select' and (month is None or year is None):
        if not quiet:
            typer.echo(f"??\tSpecify both month and year for the {typer.style(name, fg=typer.colors.GREEN)} workflow")
        raise typer.Exit(code=1)

    config = parse_config(config_path=config_path)
    if not quiet:
        typer.echo(f"🚀\tRunning {typer.style(name, fg=typer.colors.GREEN)} workflow")

        typer.echo(f"📇\tE-REDES client info: "
                   f"NIF: {typer.style(config['eredes']['nif'], fg=typer.colors.GREEN, bold=True)}, "
                   f"CPE: {typer.style(config['eredes']['cpe'], fg=typer.colors.GREEN, bold=True)}")

    logger.info(f"------ NEW ERS SESSION ------")
    logger.info(f"Session ID: {uuid}")
    logger.info(f"Running the {name} workflow")
    logger.info(f"Retrieving data for the month of {month} and year {year}")
    logger.info(f"Database connections: {db}")
    logger.info(f"Running in quiet mode: {quiet}")
    logger.info(f"Output directory: {output}")
    logger.info(f"Configuration:")
    for key, value in flatten_config(config).items():
        if 'pwd' in key or 'token' in key:
            logger.info(f"{key}: {'*' * len(value)}")
        else:
            logger.info(f"{key}: {value}")

    bot = EredesScraper(
        nif=config['eredes']['nif'],
        password=config['eredes']['pwd'],
        cpe_code=config['eredes']['cpe'],
        quiet=quiet,
        headless=headless,
        uuid=uuid,
        debug=debug
    )

    match name:
        case 'current':
            bot.run(month=date.month, year=date.year)

        case 'previous':
            bot.run(month=date.month - 1, year=date.year)

        case 'select':
            bot.run(month=month, year=year)

        case _:
            if not quiet:
                typer.echo(f"??\tWorkflow {typer.style(name, fg=typer.colors.GREEN)} not supported")
            raise typer.Exit(code=1)

    for conn in db:
        match conn:
            case 'influxdb':
                client = InfluxDB(
                    token=config['influxdb']['token'],
                    org=config['influxdb']['org'],
                    host=config['influxdb']['host'],
                    port=config['influxdb']['port'],
                    bucket=config['influxdb']['bucket'],
                    quiet=quiet)
                client.connect()
                client.load(source_data=bot.dwnl_file, cpe_code=config['eredes']['cpe'], delta=delta)
                if not quiet:
                    typer.echo(f"📈\tLoaded data from {bot.dwnl_file} into the InfluxDB database")
            case None:
                pass

            case '':
                pass

            case _:
                if not quiet:
                    typer.echo(f"??\tDatabase {typer.style(db, fg=typer.colors.GREEN)} not supported")

    if not keep:
        try:
            bot.dwnl_file.unlink()
            Path.rmdir(bot.tmp)
            if not quiet:
                typer.echo(f"💀\tRemoved the source data file and the staging area: {bot.dwnl_file}")

            result = ERSSession(
                session_id=bot.session_id,
                workflow=name,
                databases=db,
                source_data=None,
                status="completed",
                timestamp=datetime.now()
            )

            return result
        except PermissionError:
            if not quiet:
                typer.echo("💥\tPermission denied to remove the source data and/or staging area for the ERS")

            result = ERSSession(
                session_id=bot.session_id,
                workflow=name,
                databases=db,
                source_data=bot.dwnl_file,
                status="completed",
                timestamp=datetime.now()
            )

            return result
    else:
        out = Path(output / bot.session_id.__str__())
        Path.mkdir(out, exist_ok=True, parents=True)
        os.rename(bot.dwnl_file, out / bot.dwnl_file.name)
        bot.dwnl_file = Path(out / bot.dwnl_file.name)
        if not quiet:
            typer.echo(f"📂\tSource data file written to: {bot.dwnl_file}")

        result = ERSSession(
            session_id=bot.session_id,
            workflow=name,
            databases=db,
            source_data=bot.dwnl_file,
            status="completed",
            timestamp=datetime.now()
        )

        return result
