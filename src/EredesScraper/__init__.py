from utils import parse_config
from pathlib import Path
from _version import get_version

minimal_config = ['EREDES_USER', 'EREDES_PASSWORD', 'EREDES_TARGET', 'EREDES_CPE']
globals().update({k: None for k in minimal_config})

config_path = Path('config')
globals().update(**parse_config(config_path))
assert 'EREDES_TARGET' in globals()


__version__ = get_version()


if __name__ == '__main__':
    print("version is: " + __version__)
