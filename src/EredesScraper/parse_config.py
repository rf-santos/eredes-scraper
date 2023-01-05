def parse_config(config_file):
    """
    The parse_config function reads the config file and returns a dictionary with all the configuration parameters.


    :return: A dictionary with the configuration parameters
    :doc-author: Ricardo Filipe dos Santos
    """
    eredes_conf = dict()

    try:
        with open(config_file, 'r') as c:
            config = c.read()
    except FileNotFoundError:
        print('Config file not found')
        exit(1)

    for line in config.splitlines():
        eredes_conf[str(line.split('=')[0].strip())] = str(line.split('=')[1].strip().strip('"').strip("'"))

    return eredes_conf
