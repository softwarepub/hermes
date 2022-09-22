# TODO this file contains only dummy implementations which in most cases will lead to a crash...
import logging
import toml


_config = {}


def configure():
    if _config:
        return

    # Load configuration if not present
    with open('pyproject.toml', 'r') as config_file:
        config_toml = toml.load(config_file)
        hermes_config = config_toml['tool']['hermes']
        _config['hermes'] = hermes_config
        _config['logging'] = hermes_config['logging']


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
