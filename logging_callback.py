import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger('mylogger')
handler = RotatingFileHandler(filename='mylogger.txt', maxBytes=2000, backupCount=5)
logger.addHandler(handler)

def callback():
    logger.warning("callback")


def main(callback):
    for _ in range(10000):
        logger.warning("main")
    callback()

main(callback)
