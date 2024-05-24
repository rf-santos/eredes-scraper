from pathlib import Path
from typer import get_app_dir

Path.mkdir(Path.home() / ".ers", exist_ok=True)
appdir = get_app_dir("ers")
global stateless
