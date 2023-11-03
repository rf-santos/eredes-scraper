import typer
import tomllib
from pathlib import Path

from eredesscraper._version import get_version

project = tomllib.loads(Path(Path(__file__).parent.parent / "pyproject.toml").resolve().read_text())

cli_header = f"""
{typer.style("E-REDES Scraper", 
             fg=typer.colors.BRIGHT_CYAN, 
             bold=True)}
{typer.style(f"Version: {typer.style(get_version(), underline=True)}", 
             bold=True)}
{typer.style(f"Authors: {project['tool']['poetry']['authors']}", 
             bold=True)}
{typer.style(f"Hompage: {typer.style(project['tool']['poetry']['homepage'],fg=typer.colors.CYAN, italic=True)}", 
             bold=True)}

{project['tool']['poetry']['description']}
"""

supported_workflows = ["current_month", "last_month", "select_month"]

supported_databases = ["influxdb"]