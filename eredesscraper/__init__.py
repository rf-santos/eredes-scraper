from pathlib import Path
from subprocess import run

from typer import get_app_dir

Path.mkdir(Path.home() / ".ers", exist_ok=True)
appdir = get_app_dir("ers")

assert run(["playwright", "install", "--with-deps", "webkit"],
           capture_output=True).returncode == 0, "Failed to install Playwright dependencies."
