from os import environ


def parse_config(config_file=None):
    """
    The parse_config function reads the config file and returns a dictionary with all the configuration parameters.


    :return: A dictionary with the configuration parameters
    :doc-author: Ricardo Filipe dos Santos
    """
    eredes_conf = {}

    try:
        with open(config_file, 'r') as c:
            config = c.read()

        for line in config.splitlines():
            eredes_conf[str(line.split('=')[0].strip())] = str(line.split('=')[1].strip().strip('"').strip("'"))

        assert eredes_conf['EREDES_TARGET'] is not None
        assert eredes_conf['EREDES_CPE'] is not None

        return eredes_conf

    except FileNotFoundError:
        print('Config file not found')
        print('Trying to read environment variables')
        pass

    finally:
        if 'EREDES_USER' in eredes_conf and eredes_conf['EREDES_USER'] is not None:
            pass
        else:
            eredes_conf['EREDES_USER'] = environ.get('EREDES_USER')

        if 'EREDES_PASSWORD' in eredes_conf and eredes_conf['EREDES_PASSWORD'] is not None:
            pass
        else:
            eredes_conf['EREDES_PASSWORD'] = environ.get('EREDES_PASSWORD')

        if 'EREDES_TARGET' in eredes_conf and eredes_conf['EREDES_TARGET'] is not None:
            pass
        else:
            eredes_conf['EREDES_TARGET'] = environ.get('EREDES_TARGET')

        if 'EREDES_CPE' in eredes_conf and eredes_conf['EREDES_CPE'] is not None:
            pass
        else:
            eredes_conf['EREDES_CPE'] = environ.get('EREDES_CPE')

        assert eredes_conf['EREDES_USER'] is not None
        assert eredes_conf['EREDES_PASSWORD'] is not None
        assert eredes_conf['EREDES_TARGET'] is not None
        assert eredes_conf['EREDES_CPE'] is not None

    return eredes_conf
