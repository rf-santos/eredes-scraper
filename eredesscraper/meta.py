import sys
import tomllib
from pathlib import Path

import typer

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
{typer.style(f"Hompage: {typer.style(project['tool']['poetry']['homepage'], fg=typer.colors.CYAN, italic=True)}",
             bold=True)}

{project['tool']['poetry']['description']}
"""

supported_workflows = ["current", "previous", "select"]

supported_databases = ["influxdb"]

if sys.platform == "win32":
    user_agent_list = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.2535.92'
    ]

else:
    user_agent_list = [
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36'
    ]

en_pt_month_map = {
    "01": "jan",
    "02": "fev",
    "03": "mar",
    "04": "abr",
    "05": "mai",
    "06": "jun",
    "07": "jul",
    "08": "ago",
    "09": "set",
    "10": "out",
    "11": "nov",
    "12": "dez",
}
