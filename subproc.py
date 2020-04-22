import logging
import os
logger = logging.getLogger(__name__)


def test(value):
    msg = '[{}] value {}'.format(os.getpid(), value)
    logger.info(msg)
