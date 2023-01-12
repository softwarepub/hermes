# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

# TODO this file contains only dummy implementations which in most cases will lead to a crash...
import logging
import toml


_config = {
    'logging': {
        'version': 1,

        'formatters': {
            'plain': { 'format': "%(message)s" },
            'logfile': { 'format': "%(created)16f:%(name)20s:%(levelname)10s | %(message)s" },
            'auditlog': { 'format': "%(asctime)s %(name)-20s  %(message)s" },
        },

        'handlers': {
            'terminal': {
                'class': "logging.StreamHandler",
                'formatter': "plain",
                'level': "INFO",
                'stream': "ext://sys.stdout",
            },

            'logfile': {
                'class': "logging.FileHandler",
                'formatter': "logfile",
                'level': "DEBUG",
                'filename': "hermes.log",
            },

            'auditfile': {
                'class': "logging.FileHandler",
                'formatter': "plain",
                'level': "DEBUG",
                'filename': "hermes-audit.md",
                'mode': "w",
            },
        },

        'loggers': {
            'cli': {'level': "DEBUG", 'handlers': ['terminal']},
            'hermes': {'level': "DEBUG", 'handlers': ['terminal', 'logfile']},
            'audit': {'level': "DEBUG", 'handlers': ['terminal', 'logfile']},
        },
    },
}


def configure():
    if 'hermes' in _config:
        return

    # Load configuration if not present
    try:
        with open('pyproject.toml', 'r') as config_file:
            config_toml = toml.load(config_file)
            hermes_config = config_toml['tool'].get('hermes', {})
            _config['hermes'] = hermes_config
            _config['logging'] = hermes_config.get('logging', _config['logging'])

    except IOError:
        pass


def get(name):
    if name not in _config:
        _config['hermes'][name] = {}
        _config[name] = _config['hermes'][name]

    return _config.get(name)


_loggers = {}


def init_logging():
    if _loggers:
        return

    # Inintialize logging system
    import logging.config

    configure()

    logging.config.dictConfig(_config['logging'])
    for log_name in _config['logging']['loggers']:
        _loggers[log_name] = logging.getLogger(log_name)


def getLogger(log_name):
    init_logging()
    if log_name not in _loggers:
        _loggers[log_name] = logging.getLogger(log_name)
    return _loggers.get(log_name)
