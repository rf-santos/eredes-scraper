import pytest
from pytz import UTC
from pathlib import Path
from eredesscraper.utils import parse_monthly_consumptions, flatten_config, flatten_keys, struct_config, parse_config, infer_type, map_month_matrix

def test_parse_monthly_consumptions():
    file_path = Path(__file__).parent / 'example.xlsx'
    cpe_code = 'PT00############04TW'
    df = parse_monthly_consumptions(file_path, cpe_code)
    assert df is not None
    assert 'cpe' in df.columns
    assert 'consumption' in df.columns
    assert df['cpe'].unique() == cpe_code
    assert df.index.tzinfo == UTC
    assert df['consumption'].dtype == float
    assert df['consumption'].sum() == 989.348

def test_flatten_config():
    d = {'a': 1, 'b': {'x': 2, 'y': 3}, 'c': 4}
    flat_d = flatten_config(d)
    assert flat_d == {'a': 1, 'b.x': 2, 'b.y': 3, 'c': 4}

def test_flatten_keys():
    d = {'a.b': 1, 'c.d': 2}
    flat_d = flatten_keys(d)
    assert flat_d == {'b': 1, 'd': 2}

def test_struct_config():
    d = {'a.b': 1, 'c.d': 2}
    struct_d = struct_config(d)
    assert struct_d == {'a': {'b': 1}, 'c': {'d': 2}}

def test_parse_config():
    config_path = Path(__file__).parent.parent / 'config.yml'
    config = parse_config(config_path)
    assert config is not None
    assert isinstance(config, dict)

def test_infer_type():
    assert infer_type('1') == 1
    assert infer_type('1.0') == 1.0
    assert infer_type('True') is True
    assert infer_type('False') is False
    assert infer_type('test') == 'test'

def test_map_month_matrix():
    from datetime import datetime
    date = datetime(2022, 1, 1)
    assert map_month_matrix(date) == (1, 1)
    date = datetime(2022, 4, 1)
    assert map_month_matrix(date) == (2, 1)
    date = datetime(2022, 7, 1)
    assert map_month_matrix(date) == (3, 1)
    date = datetime(2022, 10, 1)
    assert map_month_matrix(date) == (4, 1)

if __name__ == '__main__':
    pytest.main()