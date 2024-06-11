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

supported_workflows = ["current", "previous", "select"]

supported_databases = ["influxdb"]

user_agent_list = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.2535.92',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
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