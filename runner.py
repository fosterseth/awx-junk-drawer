import logging
from multiprocessing import Pool
import os
from subproc import test

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    import logging.config
    import yaml

    path = 'logging.yaml'
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.load(f.read())
        logging.config.dictConfig(config)

    test('begin')

    p = Pool(4)
    p.map(test, [1, 2, 3, 4])

    test('end')
