from parse_config import parse_config
from pathlib import Path

config_path = Path('config')
globals().update(**parse_config(config_path))

assert 'EREDES_TARGET' in globals()
