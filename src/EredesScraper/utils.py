from astrapy.rest import create_client, http_methods
import uuid
from os import environ
import toml
from collections.abc import MutableMapping


def flatten(d, parent_key='', sep='.') -> dict:
    """
    The flatten function takes a dictionary and flattens it into a single level.
    For example, if the input is:
    {'a': 1, 'b': {'x': 2, 'y': 3}, 'c': 4}
    then the output will be:
    {'a': 1, 'b.x': 2, 'b.y', 3 ,'c', 4}

    :param d: Pass the dictionary to be flattened
    :param parent_key='': Keep track of the parent key
    :param sep='.': Separate the keys in the nested dictionary
    :return: A dictionary with all the keys and values from a nested dictionary
    :doc-author: Ricardo Filipe dos Santos
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def keys2env(d: dict, sep: str = '.', keep_level: int = -1) -> dict:
    """
    The keys2env function takes a dictionary and returns a new dictionary with the keys split by the specified separator.
    The keep_level parameter specifies which list index to keep after key.split(),
    by default keeps last item of split.

    :param d:dict: Specify the dictionary that is to be converted
    :param sep:str='.': Split the key string into a list of substrings
    :param keep_level:int=-1: Keep only the `keep_level` index of the split key name
    :return: A dictionary with the modified keys of `d`
    :doc-author: Ricardo Filipe dos Santos
    """
    items = {}
    for k, v in d.items():
        items[k.split(sep)[keep_level]] = v

    return items


def parse_config(config_file=None):
    """
    The parse_config function reads the config file and returns a dictionary with all the configuration parameters.


    :return: A dictionary with the configuration parameters
    :doc-author: Ricardo Filipe dos Santos
    """
    eredes_conf = {}

    if config_file:
        eredes_conf = keys2env(flatten(toml.load(config_file)))

    return eredes_conf


def astra_conn(astra_config: dict):
    ASTRA_DB_ID = astra_config['ASTRA_DB_ID']
    ASTRA_DB_REGION = astra_config['ASTRA_DB_REGION']
    ASTRA_DB_APPLICATION_TOKEN = astra_config['ASTRA_DB_APPLICATION_TOKEN']
    # ASTRA_DB_KEYSPACE = astra_config['ASTRA_DB_KEYSPACE']

    astra_client = create_client(
        astra_database_id=ASTRA_DB_ID,
        astra_database_region=ASTRA_DB_REGION,
        astra_application_token=ASTRA_DB_APPLICATION_TOKEN
    )

    return astra_client
