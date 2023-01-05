from logging import getLogger, StreamHandler, DEBUG
from sys import stdout

class EredesAgent():
    def __init__(self, config):
        self.config = config
        self.log = getLogger('eredes-agent')
        self.log.setLevel(DEBUG)
        self.log.addHandler(StreamHandler(stream=stdout))

        self.log.info('Initializing Eredes Agent')

        self.log.info('Loading Eredes API')

        self.log.info('Loading Eredes Scraper')
