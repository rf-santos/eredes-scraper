from pathlib import Path
from typing import Optional

import typer
import yaml

from eredesscraper.utils import parse_config, flatten_config, struct_config, infer_type
from eredesscraper.workflows import switchboard
from eredesscraper.meta import cli_header, supported_workflows, supported_databases
from eredesscraper._version import get_version

appdir = typer.get_app_dir(app_name="ers")
config_path = Path(appdir) / "cache" / "config.yml"

app = typer.Typer(name="ers",
                  help=cli_header,
                  add_completion=False,
                  add_help_option=True,
                  no_args_is_help=True,
                  epilog="For more information, please visit https://github.com/rf-santos/eredes-scraper",
                  context_settings={"allow_extra_args": True})

@app.command(help="Show the current version")
def version():
    """Show the current version"""
    typer.echo(f"Version: {get_version()}")


@app.command(help="Initialize the program with a CLI wizard")
def init():
    """Initialize the program with a CLI wizard"""

    typer.echo("Welcome to E-REDES Scraper!")
    typer.echo("Please follow the instructions to set up the program.")
    typer.echo("Press Ctrl+C at any time to exit the wizard.")
    typer.echo("")
    typer.echo("First, we need to set up the config file. "
               "See the template `config.yml` at github.com/rf-santos/eredes-scraper for reference.")
    typer.echo("")
    typer.echo("Please enter the path to the config file:")
    config_path = typer.prompt("Path to config file", default="config.yml")
    assert Path(config_path).exists(), "File not found. Please check the path and try again."
    assert Path(config_path).is_file(), "Please enter a valid file path."
    load(config_path)
    typer.echo("Config file loaded successfully.")


@app.command(help="Run the scraper workflow. Can directly load data onto supported databases.")
def run(workflow: str = typer.Option("current_month",
                                     "--workflow", "-w",
                                     help=f"Specify one of the supported workflows: {supported_workflows}"),
        db: str = typer.Option("influxdb",
                               "--database", "--db", "-d",
                               help=f"Specify one of the supported databases: {supported_databases}"),
        month: Optional[int] = typer.Option(None,
                                            "--month", "-m",
                                            help="Specify the month to load (1-12). "
                                                 "[Required for `select_month` workflow]",
                                            show_default=False),
        delta: Optional[bool] = typer.Option(False,
                                             "--delta", "-D",
                                             help="Load only the most recent data points")):
    """Run a workflow from a config file"""
    config = Path(appdir) / "cache" / "config.yml"
    assert Path(
        config).exists(), f"Config file not found. Run {typer.style('ers config load </path/to/config.yml>', fg=typer.colors.GREEN)} to load it."

    if db is None:
        db = ""

    switchboard(
        config_path=config.resolve(),
        name=workflow,
        db=db,
        month=month,
        delta=delta
    )


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
                                      help="Path to the config file"
                                      )
         ):
    try:
        config_path = Path(config).resolve()

        Path.mkdir(Path(appdir) / "cache", parents=True, exist_ok=True)

        cache = Path(appdir) / "cache"

        typer.echo(f"⚙️\tLoading configuration from file: {config_path}")

        with open(config_path, "r") as f:
            tmp_config = yaml.safe_load(f)

        with open(cache / "config.yml", "w") as f:
            yaml.dump(tmp_config, f)

        typer.echo("✅\tConfig file loaded successfully.")

    except FileNotFoundError:
        typer.echo("💥\tFile not found. Please check the path and try again.")
        raise typer.Exit(code=1)


@config_app.command(help="Show the current configuration")
def show():
    """Show the current configuration"""
    try:
        config = parse_config(Path(appdir) / "cache" / "config.yml")
        typer.echo("")
        typer.echo("⚙️\tCurrent configuration (cached):")
        typer.echo("")
        typer.echo(yaml.dump(config), color=True)
    except FileNotFoundError:
        typer.echo("No config file found. Please run `ers config load /path/to/config.yml` to set a config file.")
        raise typer.Exit(code=1)


@config_app.command(help="Set a configuration value.\nUsage: ers config set <key>[.<subkey>] <value>",
                    options_metavar="<KEY>[.<SUBKEY>] <VALUE>",
                    no_args_is_help=True,
                    epilog="Example: ers config set influxdb.host \"http://localhost\"")
def set(key: str, value: str):
    """
    Set a configuration value

    This command is not idempotent, meaning that it will overwrite the current value of the key in the cached config.

    Infers the type of the value.
    """
    value = infer_type(value)

    try:
        config = flatten_config(parse_config(Path(appdir) / "cache" / "config.yml"))
    except FileNotFoundError:
        typer.echo("No config file found. Please run `ers config file </path/to/config.yml>` to set a config file.")
        raise typer.Exit(code=1)

    assert key in config.keys(), f"Unsupported key {key} not found in config file.\nKeys: {list(config.keys())}"

    config[key] = value

    with open(Path(appdir) / "cache" / "config.yml", "w") as f:
        yaml.dump(struct_config(config), f)

    typer.echo(f"✅\tKey {typer.style(key, fg=typer.colors.GREEN)} set to {typer.style(value, fg=typer.colors.GREEN)}.")


if __name__ == "__main__":
    app()
