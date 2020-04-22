import logging


config1 = {
    'version': 1,
    'formatters' : {
        'simple1': {
            'format': '%(process)d %(message)s',
        },
        'simple2': {
            'format': '%(asctime)s %(levelname)-8s %(name)s %(message)s',
        },
    },
    'handlers': {
        'console1': {
            '()': 'logging.StreamHandler',
            'level': 'DEBUG',
            'filters': [],
            'formatter': 'simple1',
        },
        'console2': {
            '()': 'logging.StreamHandler',
            'level': 'DEBUG',
            'filters': [],
            'formatter': 'simple2',
        },
    },
    'loggers': {
        'main': {
            'handlers': ['console1'],
            'level': 'DEBUG',
        },
        'main.logger2': {
            'handlers': ['console2'],
            'propagate': True,
            'level': 'DEBUG',
        }
    }
}
