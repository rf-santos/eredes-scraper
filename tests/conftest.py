import os
from pathlib import Path
from screeninfo import Monitor
from unittest.mock import patch

import pytest


@pytest.fixture(scope='session')
def db_path(request):
    db_path = Path(__file__).parent / 'test.db'
    yield db_path.absolute().as_posix()
    request.addfinalizer(lambda: os.remove(db_path))


@pytest.fixture(scope='session')
def config_path():
    return Path(Path(__file__).parent.parent / 'config.yml').resolve()


@pytest.fixture
def mock_monitor():
    return [Monitor(x=0, y=0, width=1920, height=1080, width_mm=509, height_mm=286, name='MockMonitor', is_primary=True)]
