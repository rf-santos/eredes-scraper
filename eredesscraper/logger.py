import logging

from eredesscraper.__init__ import configdir

logfile = configdir / "ers.log"

logger = logging.getLogger("ers")
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler(logfile)
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)