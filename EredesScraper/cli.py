import pathlib
from pathlib import Path
from typing import Optional

import typer
import yaml
from click import Choice
from typing_extensions import Annotated

from EredesScraper.utils import parse_config, flatten_config, struct_config, infer_type
from EredesScraper.workflows import switchboard

appdir = typer.get_app_dir(app_name="ers")
config_path = Path(appdir) / "cache" / "config.yml"

app = typer.Typer(name="ers",
                  help="EredesScraper CLI",
                  add_completion=False,
                  add_help_option=True,
                  no_args_is_help=True,
                  epilog="For more information, please visit https://github.com/rf-santos/eredes-scraper")


@app.command(help="Initialize the program with a CLI wizard")
def init():
    """Initialize the program with a CLI wizard"""
    typer.echo("Welcome to EredesScraper!")
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
    config = parse_config(config_path)
    typer.echo("Config file loaded successfully.")
    typer.echo("")
    typer.echo("Please enter the workflow to run:")
    workflow = typer.prompt("Workflow", default="current_month_consumption", show_choices=True,
                            type=Choice(["current_month_consumption", "last_month_consumption"]))
    typer.echo("")
    typer.echo("Initializing the program...")
    typer.echo("")


@app.command(help="Run the scraper workflow. Can directly load data onto supported databases.")
def run(config: Annotated[Optional[pathlib.Path], typer.Argument()] = Path(appdir) / "cache" / "config.yml",
        workflow: Annotated[Optional[str], typer.Argument()] = "current_month_consumption",
        db: Annotated[Optional[str], typer.Argument()] = None):
    """Run a workflow from a config file"""
    assert Path(config).exists(), f"Config file not found. Run {typer.style('ers config load </path/to/config.yml>', fg=typer.colors.GREEN)} to load it."

    if db is None:
        db = ""

    switchboard(
        config_path=config.resolve(),
        name=workflow,
        db=db
    )


config_app = typer.Typer(name="config",
                         help="EredesScraper CLI configuration",
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
        typer.echo("No config file found. Please run `ers config file /path/to/config.yml` to set a config file.")
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
