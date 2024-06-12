from pathlib import Path
from typing import Optional

import typer
import yaml

from eredesscraper.utils import parse_config, validate_config, flatten_config, struct_config, infer_type
from eredesscraper.workflows import switchboard
from eredesscraper.meta import cli_header, supported_workflows, supported_databases
from eredesscraper._version import get_version
from eredesscraper.server import start_api_server
from eredesscraper.backend import db_path

appdir = typer.get_app_dir(app_name="ers")
config_path = Path(appdir) / "cache" / "config.yml"

app = typer.Typer(name="ers",
                  help=cli_header,
                  add_completion=False,
                  add_help_option=True,
                  no_args_is_help=True,
                  epilog="For more information, please visit https://github.com/rf-santos/eredes-scraper",
                  pretty_exceptions_show_locals=False,
                  context_settings={"allow_extra_args": True})


@app.callback()
def main(ctx: typer.Context, quiet: bool = typer.Option(False, "--quiet", "-q", help="Run in non-interactive mode")):
    """Main entry point for the CLI."""
    ctx.ensure_object(dict)
    ctx.obj["quiet"] = quiet


@app.command(help="Show the current version")
def version(ctx: typer.Context):
    """Show the current version"""
    if not ctx.obj["quiet"]:
        typer.echo(f"Version: {get_version()}")


@app.command(help="Get information about the available workflows and databases")
def info(ctx: typer.Context):
    """Get information about the available workflows and databases"""
    if not ctx.obj["quiet"]:
        typer.echo(f"Supported workflows: {supported_workflows}")
        typer.echo(f"Supported databases: {supported_databases}")


@app.command(help="Run the scraper workflow. Can directly load data onto supported databases.")
def run(workflow: str = typer.Option("current",
                                     "--workflow", "-w",
                                     help=f"Specify one of the supported workflows: {supported_workflows}"),
        db: str = typer.Option(None,
                               "--database", "--db", "-d",
                               help=f"Specify a comma separated list of databases: {supported_databases}"),
        month: Optional[int] = typer.Option(None,
                                            "--month", "-m",
                                            help="Specify the month to load (1-12). "
                                                 "[Required for `select` workflow]",
                                            show_default=False),
        year: Optional[int] = typer.Option(None, "--year", "-y",
                                           help="Specify the year to load (YYYY). "
                                                "[Required for `select` workflow]",
                                           show_default=False),
        delta: Optional[bool] = typer.Option(False,
                                             "--delta", "-D",
                                             help="Load only the most recent data points"),
        keep: Optional[bool] = typer.Option(False,
                                            "--keep", "-k",
                                            help="If set, keeps the source data file after loading",
                                            show_default=False),
        output: Optional[str] = typer.Option(Path.cwd() / ".ers", "--output", "-o",
                                             help="Specify the output folder path",
                                             show_default=True),
        headless: Optional[bool] = typer.Option(True,
                                                "--headless", "-H",
                                                help="Disable headless mode"),
        ctx: typer.Context = typer.Option(None, callback=main)):
    """Run a workflow from a config file"""
    config = Path(appdir) / "cache" / "config.yml"
    assert Path(
        config).exists(), f"Config file not found. "
    f"Run {typer.style('ers config load </path/to/config.yml>', fg=typer.colors.GREEN)} to load it."

    if db is None:
        db = []
    else:
        db = db.strip().split(",")
        # remove any whitespace
        db = [x.strip() for x in db]

    result = switchboard(
        config_path=config.resolve(),
        name=workflow,
        db=db,
        month=month,
        year=year,
        delta=delta,
        keep=keep,
        headless=headless,
        quiet=ctx.obj["quiet"]
    )

    if not ctx.obj["quiet"]:
        typer.echo(result)


config_app = typer.Typer(name="config",
                         help="E-REDES Scraper CLI configuration",
                         add_completion=False,
                         add_help_option=True,
                         no_args_is_help=True)

app.add_typer(config_app, name="config", help="Interact with the program configuration")


@config_app.command(help="Loads a config file into the program")
def load(config: str = typer.Argument(resolve_path=True,
                                      exists=True,
                                      file_okay=True,
                                      dir_okay=False,
                                      writable=True,
                                      readable=True,
                                      help="Path to the config file"),
         ctx: typer.Context = typer.Option(None, callback=main)):
    try:
        config_path = Path(config).resolve()

        if not validate_config(config_path):
            if not ctx.obj["quiet"]:
                typer.echo("💥\tInvalid configuration file. Please check the configuration schema and try again.")
            raise typer.Exit(code=1)

        Path.mkdir(Path(appdir) / "cache", parents=True, exist_ok=True)

        cache = Path(appdir) / "cache"
        if not ctx.obj["quiet"]:
            typer.echo(f"⚙️\tLoading configuration from file: {config_path}")

        with open(config_path, "r") as f:
            tmp_config = yaml.safe_load(f)

        with open(cache / "config.yml", "w") as f:
            yaml.dump(tmp_config, f)
        if not ctx.obj["quiet"]:
            typer.echo("✅\tConfig file loaded successfully.")

    except FileNotFoundError:
        if not ctx.obj["quiet"]:
            typer.echo("💥\tFile not found. Please check the path and try again.")
        raise typer.Exit(code=1)


@config_app.command(help="Show the current configuration")
def show(ctx: typer.Context = typer.Option(None, callback=main)):
    """Show the current configuration"""
    try:
        config = parse_config(Path(appdir) / "cache" / "config.yml")
        if not ctx.obj["quiet"]:
            typer.echo("")
            typer.echo("⚙️\tCurrent configuration (cached):")
            typer.echo("")
            typer.echo(yaml.dump(config), color=True)
    except FileNotFoundError:
        if not ctx.obj["quiet"]:
            typer.echo("No config file found. Please run `ers config load /path/to/config.yml` to set a config file.")
        raise typer.Exit(code=1)


@config_app.command(help="Set a configuration value.\nUsage: ers config set <key>[.<subkey>] <value>",
                    options_metavar="<KEY>[.<SUBKEY>] <VALUE>",
                    no_args_is_help=True,
                    epilog="Example: ers config set influxdb.host \"http://localhost\"")
def set(key: str, value: str, ctx: typer.Context = typer.Option(None, callback=main)):
    """
    Set a configuration value

    This command is not idempotent, meaning that it will overwrite the current value of the key in the cached config.

    Infers the type of the value.
    """
    value = infer_type(value)

    try:
        config = flatten_config(parse_config(Path(appdir) / "cache" / "config.yml"))
    except FileNotFoundError:
        if not ctx.obj["quiet"]:
            typer.echo("No config file found. Please run `ers config file </path/to/config.yml>` to set a config file.")
        raise typer.Exit(code=1)

    assert key in config.keys(), f"Unsupported key {key} not found in config file.\nKeys: {list(config.keys())}"

    config[key] = value

    with open(Path(appdir) / "cache" / "config.yml", "w") as f:
        yaml.dump(struct_config(config), f)
    if not ctx.obj["quiet"]:
        typer.echo(
            f"✅\tKey {typer.style(key, fg=typer.colors.GREEN)} set to {typer.style(value, fg=typer.colors.GREEN)}.")


@app.command(help="Start the application webserver")
def server(
        ctx: typer.Context,
        port: Optional[int] = typer.Option(8778, "--port", "-p",
                                           help="Specify the port to run the webserver on"),
        host: Optional[str] = typer.Option("localhost", "--host", "-H",
                                           help="Specify the host to run the webserver on"),
        reload: Optional[bool] = typer.Option(False, "--reload", "-r",
                                              help="Enable auto-reload"),
        debug: Optional[bool] = typer.Option(False, "--debug", "-d",
                                             help="Enable debug mode"),
        storage: Optional[str] = typer.Option(db_path.parent.absolute().as_posix(), "--storage", "-S",
                                              help="Specify the storage path to persist the API state")):
    """Start the application webserver"""

    try:
        Path.mkdir(Path(storage), parents=True, exist_ok=True)
    except NotADirectoryError:
        typer.echo("💥\tInvalid storage path. Please check the path and try again.")
        raise typer.Exit(code=1)

    if not ctx.obj["quiet"]:
        typer.echo("Starting the webserver...")
        typer.echo(f"Running in stateful mode. This will persist data in {storage}")

    start_api_server(port=port, host=host, reload=reload, debug=debug)


if __name__ == "__main__":
    app()
