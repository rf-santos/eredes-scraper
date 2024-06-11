# package imports
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4
import os

import typer

from eredesscraper.agent import EredesScraper
from eredesscraper.db_clients import InfluxDB
from eredesscraper.utils import parse_config

user_config_path = Path().home() / ".ers"
Path.mkdir(user_config_path, exist_ok=True)

date = datetime.now()


class ERSSession():
    def __init__(self, session_id: str, workflow: str, databases: list, source_data: Path | None, status: str,
                 timestamp: datetime):
        self.session_id = session_id
        self.workflow = workflow
        self.databases = databases
        self.source_data = source_data
        self.staging_area = source_data.parent if source_data else None
        self.status = status
        self.timestamp = timestamp
        self.task_id = None

    def set_task_id(self, task_id: str):
        self.task_id = task_id

    def get_task_id(self):
        return self.task_id

    def __str__(self):
        return f"Session ID: {self.session_id}\nWorkflow: {self.workflow}\nDatabases: {self.databases}\nSource Data: {self.source_data}\nStaging Area: {self.staging_area}\nStatus: {self.status}\nTimestamp: {self.timestamp}\n"

    def __repr__(self):
        return f"ERSSession(session_id={self.session_id}, workflow={self.workflow}, databases={self.databases}, source_data={self.source_data}, staging_area={self.staging_area}, status={self.status}, timestamp={self.timestamp})"

    def __eq__(self, other):
        if not isinstance(other, ERSSession):
            return NotImplemented
        return self.session_id == other.session_id and self.workflow == other.workflow and self.databases == other.databases and self.source_data == other.source_data and self.staging_area == other.staging_area and self.status == other.status and self.timestamp == other.timestamp

    def __ne__(self, other):
        if not isinstance(other, ERSSession):
            return NotImplemented
        return self.session_id != other.session_id or self.workflow != other.workflow or self.databases != other.databases or self.source_data != other.source_data or self.staging_area != other.staging_area or self.status != other.status or self.timestamp != other.timestamp

    def __lt__(self, other):
        if not isinstance(other, ERSSession):
            return NotImplemented
        return self.timestamp < other.timestamp

    def __le__(self, other):
        if not isinstance(other, ERSSession):
            return NotImplemented
        return self.timestamp <= other.timestamp

    def __gt__(self, other):
        if not isinstance(other, ERSSession):
            return NotImplemented
        return self.timestamp > other.timestamp

    def __ge__(self, other):
        if not isinstance(other, ERSSession):
            return NotImplemented
        return self.timestamp >= other.timestamp

    def __hash__(self):
        return hash((self.session_id, self.workflow, self.databases, self.source_data, self.staging_area, self.status,
                     self.timestamp))


def switchboard(name: str, db: list, config_path: Path, month: int = date.month, year: int = date.year,
                delta: bool = False, keep: bool = False, quiet: bool = False, output: Path = Path.home() / ".ers",
                uuid: uuid4 = uuid4(), headless: bool = True) -> ERSSession:
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
    """

    date = datetime.now()

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
        
    bot = EredesScraper(
                nif=config['eredes']['nif'],
                password=config['eredes']['pwd'],
                cpe_code=config['eredes']['cpe'],
                quiet=quiet,
                headless=headless,
                uuid=uuid
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
        os.unlink(bot.dwnl_file)
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
