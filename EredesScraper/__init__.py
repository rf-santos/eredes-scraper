from EredesScraper._version import get_version
from EredesScraper.agent import EredesScraper
from EredesScraper.utils import parse_config
from EredesScraper.db_clients import InfluxDB
from EredesScraper.workflows import run


version = get_version()

__version__ = version


if __name__ == '__main__':
    print("version is: " + __version__)
