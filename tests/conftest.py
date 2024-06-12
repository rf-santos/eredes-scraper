import os
from pathlib import Path

import pytest


@pytest.fixture(scope='session')
def db_path(request):
    db_path = Path(__file__).parent / 'test.db'
    yield db_path.absolute().as_posix()
    request.addfinalizer(lambda: os.remove(db_path))


@pytest.fixture(scope='session')
def config_path():
    return Path(Path(__file__).parent.parent / 'config.yml').resolve()
