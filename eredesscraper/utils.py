import os
import time
from collections.abc import MutableMapping
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from typing import Union

import pandas as pd
import yaml
from selenium.webdriver.common.by import By


def parse_monthly_consumptions(file_path: Path, cpe_code: str) -> pd.DataFrame:
    """
    The parse_file function takes a XLSX file path retrieved from E-REDES and returns
    a pandas DataFrame with the parsed data.
    An example for the retrieved file can be found in the `tests` folder.
    TZ is set to Europe/Lisbon
    Parsing rules:
    - The first 7 lines are skipped
    - The table has 3 columns: Date, Time and Value
    - The Date is "date", the Time is "time", the Value is "consumption"
    - The "date" and "time" columns are merged into a single column named "date_time"

    :param file_path: Specify the Excel (.XLSX) file path of the file to be parsed
    :type file_path: pathlib.Path
    :param cpe_code: Specify the CPE code to be added to the DataFrame
    :type cpe_code: str
    :return: A pandas DataFrame with the parsed data
    :doc-author: Ricardo Filipe dos Santos
    """

    df = pd.read_excel(
        file_path,
        skiprows=7,
        parse_dates=[[0, 1]],
        names=['date', 'time', 'consumption'],
        dtype={'consumption': float},
        decimal=',',
        thousands='.'
    )

    # add the cpe code from the config file to all rows
    df['cpe'] = cpe_code

    # add the date_time column
    df['date_time'] = df['date_time'].dt.tz_localize('Europe/Lisbon', ambiguous=True)
    df.set_index('date_time', inplace=True)

    return df


def flatten_config(d, parent_key='', sep='.') -> dict:
    """
    The flatten_config function takes a dictionary and flattens it into a single level.
    For example, if the input is:
    {'a': 1, 'b': {'x': 2, 'y': 3}, 'c': 4}
    then the output will be:
    {'a': 1, 'b.x': 2, 'b.y', 3 ,'c', 4}

    :param d: Pass the dictionary to be flattened
    :type d: dict
    :param parent_key: Keep track of the parent key
    :type parent_key: str
    :param sep: Separate the keys in the nested dictionary
    :type sep: str
    :return: A dictionary with all the keys and values from a nested dictionary
    :doc-author: Ricardo Filipe dos Santos
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten_config(v, new_key.lower(), sep=sep).items())
        else:
            items.append((new_key.lower(), v))
    return dict(items)


def flatten_keys(d: dict, sep: str = '.', keep_level: int = -1) -> dict:
    """
    The flatten_keys function takes a dictionary and returns a new dictionary with the keys
    split by the specified separator.
    The keep_level parameter specifies which list index to keep after key.split(),
    by default keeps last item of split.

    :param d: Specify the dictionary that is to be converted
    :type d: dict
    :param sep: Split the key string into a list of substrings
    :type sep: str
    :param keep_level: Keep only the `keep_level` index of the split key name
    :type keep_level: int
    :return: A dictionary with the modified keys of `d`
    :doc-author: Ricardo Filipe dos Santos
    """
    items = {}
    for k, v in d.items():
        items[k.split(sep)[keep_level]] = v

    return items


def struct_config(d: dict, sep: str = ".") -> dict:
    """
    The struct_config function takes a dictionary as the one given by the flatten_config function and structures it
    with nested dicts, useful to dump as YAML file.

    :param d: Specify the dictionary that is to be converted. (typically, a flattened dictionary)
    :type d: dict
    :param sep: Specify the separator used in the flattened dictionary.
    :type sep: str
    :return: A dictionary with the modified keys of `d`
    :doc-author: Ricardo Filipe dos Santos
    """
    items = {}
    for k, v in d.items():
        keys = k.split(sep)
        if len(keys) == 1:
            items[k] = v
        else:
            if keys[0] not in items:
                items[keys[0]] = {}
            items[keys[0]][keys[1]] = v

    return items


def parse_config(config_path: Path = Path.cwd() / "config.yml") -> dict:
    """
    Parses a YAML configuration file and returns its contents as a dictionary.

    Args:
        config_path (pathlib.Path): The path to the YAML configuration file. Defaults to the current working directory.

    Returns:
        dict: The contents of the YAML configuration file as a dictionary.
    """
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config


def save_screenshot(driver: webdriver, path: str = '.', name: str = 'screenshot') -> None:
    """
    Saves a screenshot of the current webpage displayed in the given WebDriver instance.

    Args:
        driver (selenium.WebDriver): The WebDriver instance to use for taking the screenshot.
        path (str, optional): The file path to save the screenshot to. Defaults to 'screenshot.png'.
    """
    try:
        path = Path(path).resolve()
        assert path.is_dir(), f"Invalid directory: {path}"
        path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        print("Permission denied to create a directory for the screenshot")

    name = name.replace(' ', '_') + '.png'

    path = path / name

    original_size = driver.get_window_size()
    required_width = driver.execute_script('return document.body.parentNode.scrollWidth')
    required_height = driver.execute_script('return document.body.parentNode.scrollHeight')
    driver.set_window_size(required_width, required_height)
    driver.find_element(By.TAG_NAME, "body").screenshot(path.__str__())
    driver.set_window_size(original_size['width'], original_size['height'])


def wait_for_download(directory, timeout, nfiles=None):
    seconds = 0
    dl_wait = True
    while dl_wait and seconds < timeout:
        time.sleep(1)
        dl_wait = False
        files = os.listdir(directory)
        if nfiles and len(files) != nfiles:
            dl_wait = True

        for fname in files:
            if fname.endswith('.crdownload'):
                dl_wait = True

        seconds += 1
    return seconds


def config2env(flat_config: dict):
    """
    The config2env function takes a dictionary and converts it to a string in the form of
    `key=value` pairs, separated by a newline character. This is then exported to the environment
    variables.

    Args:
        flat_config (dict): Specify the dictionary to be converted
    Returns:
        None
    """
    for k, v in flat_config.items():
        os.environ[k.upper()] = str(v)


def infer_type(value: str) -> Union[str, int, float, bool]:
    """Infer the type of a string value.

    Args:
        value (str): The value to be inferred.

    Returns:
        Union[str, int, float, bool]: The inferred value.
    """
    if value.isnumeric():
        return int(value)
    elif value.lower() in ["True", "False", "true", "false", "yes", "no", "y", "n", "1", "0"]:
        return bool(value)
    elif value.replace(".", "", 1).isnumeric():
        return float(value)
    else:
        return value


def map_month_matrix(date: datetime) -> tuple:
    """
    The map_month_matrix function takes a month name and returns the (row, column) coordinates as a tuple.
    This maps to the month selection popup table in the E-REDES website.
    The table is a 4x3 matrix, with the months in the following order:
    January, February, March
    April, May, June
    July, August, September
    October, November, December

    Args:
        date (datetime.datetime): Specify the month to be mapped
    Returns:
        tuple: The (row, column) coordinates of the month in the table
    """
    if date.month <= 3:
        row = 1
    elif date.month <= 6:
        row = 2
    elif date.month <= 9:
        row = 3
    else:
        row = 4

    if date.month % 3 == 0:
        column = 3
    else:
        column = date.month % 3

    return row, column
