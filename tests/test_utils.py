from unittest.mock import Mock, call, patch

import pytest

from eredesscraper.utils import *


def test_parse_readings_influx():
    file_path = Path(__file__).parent / 'example.xlsx'
    cpe_code = 'PT00############04TW'
    df = readings2df(file_path, cpe_code)
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


def test_parse_config(config_path):
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


def test_map_year_steps():
    from datetime import datetime

    # Test with current year
    current_year = datetime.now().year
    assert map_year_steps(datetime(current_year, 1, 1)) == 0

    # Test with previous year
    previous_year = current_year - 1
    assert map_year_steps(datetime(previous_year, 1, 1)) == 1

    # Test with future year
    future_year = current_year + 1
    assert map_year_steps(datetime(future_year, 1, 1)) == -1


def test_file2blob():
    file_path = Path(__file__).parent / 'example.xlsx'
    blob = file2blob(file_path)
    assert isinstance(blob, bytes)
    assert len(blob) > 0
    # Add more assertions if needed


def test_pw_nav_year_back():
    # Create a mock Page object
    mock_page = Mock()

    test_date = datetime(2020, 1, 1)

    # Set the return value of get_by_text and is_visible methods
    mock_page.get_by_text.return_value.is_visible.return_value = False

    # Call the function with the mock Page object and a datetime object
    pw_nav_year_back(test_date, mock_page)

    # Assert that the click method was called once
    assert mock_page.get_by_role.call_count == 1
    assert mock_page.get_by_role.call_args == call("button", name="Ano anterior (Control + left)")

    # Reset the mock Page object
    mock_page.reset_mock()

    # Set the return value of get_by_text and is_visible methods
    mock_page.get_by_text.return_value.is_visible.return_value = True

    # Call the function with the mock Page object and a datetime object
    pw_nav_year_back(test_date, mock_page)

    # Assert that the click method was not called
    assert mock_page.get_by_role.call_count == 0


def test_db_conn(db_path):
    assert db_conn(db_path) is True


def test_get_screen_resolution(mock_monitor):
    with patch('screeninfo.get_monitors', return_value=mock_monitor) as mock_get_monitors:
        resolution = get_screen_resolution()
        assert mock_get_monitors.called, "get_monitors was not called."
        assert resolution == (1920, 1080), "Expected resolution did not match"


if __name__ == '__main__':
    pytest.main()
