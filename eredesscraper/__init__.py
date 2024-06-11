from pathlib import Path
from typer import get_app_dir
from subprocess import run

Path.mkdir(Path.home() / ".ers", exist_ok=True)
appdir = get_app_dir("ers")

assert run(["playwright", "install", "--with-deps", "webkit"], capture_output=True).returncode == 0
