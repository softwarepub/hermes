# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import logging
import pathlib

import toml

# This is the default logging configuration, required to see log output at all.
#  - Maybe it could possibly somehow be a somewhat good idea to move this into an own module ... later perhaps
_logging_config = {
    'version': 1,

    'formatters': {
        'plain': {'format': "%(message)s"},
        'logfile': {'format': "%(created)16f:%(name)20s:%(levelname)10s | %(message)s"},
        'auditlog': {'format': "%(asctime)s %(name)-20s  %(message)s"},
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
}

# This dict caches all the different configuration sections already loaded
_config = {
    # We need some basic logging configuration to get logging up and running at all
    'logging': _logging_config,
}


def configure(config_path: pathlib.Path):
    """
    Load the configuration from the given path as global hermes configuration.

    :param config_path: The path to a TOML file containing HERMES configuration.
    """
    if 'hermes' in _config:
        return

    # Load configuration if not present
    try:
        with open(config_path, 'r') as config_file:
            hermes_config = toml.load(config_file)
            _config['hermes'] = hermes_config
            _config['logging'] = hermes_config.get('logging', _config['logging'])

    # Exceptions are currently handled gracefully. Is this okay?
    except FileNotFoundError:
        print(f"Configuration not present at {config_path}.")

    except KeyError:
        print(f"Invalid configuration at {config_path}, no 'hermes' section found.")


def get(name: str) -> dict:
    """
    Retrieve the configuration dict for a certain sub-system (i.e., a section from the config file).

    The returned dict comes directly from the cache.
    I.e., it is possible to do the following *stunt* to inject default values:

    .. code: python

        my_config = config.get('my-config')
        my_config.update({ 'default': 'values' })

    :param name: The section to retrieve.
    :return: The loaded configuration data or an empty dictionary.
    """

    if name not in _config:
        # If configuration is not present, create it.
        if name not in _config['hermes']:
            _config['hermes'][name] = {}
        _config[name] = _config['hermes'][name]

    elif not _config['hermes'][name] is _config[name]:
        # If a configuration was loaded, after the defaults were set, update it.
        _config[name].update(_config['hermes'].get('name', {}))

    return _config.get(name)


# Might be a good idea to move somewhere else (see comment for _logging_config)?
_loggers = {}


def init_logging():
    if _loggers:
        return

    # Inintialize logging system
    import logging.config

    logging.config.dictConfig(_config['logging'])
    for log_name in _config['logging']['loggers']:
        _loggers[log_name] = logging.getLogger(log_name)


def getLogger(log_name):
    init_logging()
    if log_name not in _loggers:
        _loggers[log_name] = logging.getLogger(log_name)
    return _loggers.get(log_name)
