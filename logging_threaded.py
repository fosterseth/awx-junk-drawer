import logging
from logging.handlers import RotatingFileHandler

import threading
import time

logger = logging.getLogger('my_logger')
handler = RotatingFileHandler("my_log.log", maxBytes=2000, backupCount=10)
logger.setLevel(10)
logger.addHandler(handler)


def write_to_log(threadID):
    for _ in range(10000):
        # time.sleep(50/1000)
        logger.debug(str(threadID) + " Hello, world!")

class myThread(threading.Thread):
    def __init__(self, threadID):
        super().__init__()
        self.threadID = threadID
    def run(self):
        write_to_log(self.threadID)

thread1 = myThread(1)
thread2 = myThread(2)

thread1.start()
thread2.start()
thread1.join()
thread2.join()
