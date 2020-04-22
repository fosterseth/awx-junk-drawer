import logging
from logging.handlers import RotatingFileHandler
import multiprocessing
import time
import os

logger = logging.getLogger('my_logger')
handler = RotatingFileHandler("my_log.log", maxBytes=2000, backupCount=10)
logger.setLevel(10)
logger.addHandler(handler)

workers = []

def write_to_log(threadID):
    for _ in range(1000):
        # time.sleep(50/1000)
        logger.debug(str(threadID) + " Hello, world!")

for i in range(2):
    p = multiprocessing.Process(target=write_to_log, args=(i,))
    workers.append(p)

for w in workers:
    w.start()

for w in workers:
    w.join()
