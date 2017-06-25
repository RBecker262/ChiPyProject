"""
myutils.py
Author: Robert Becker
Date: June 25, 2017
Purpose: to house various common utilities

load_config_file - loads config file into an object and returns
get_config_value - retrieves value for section/key specified
"""

import configparser


class ConfigLoadError(ValueError):
    pass


class ConfigKeyError(ValueError):
    pass


def load_config_file(config_file, logger):
    """
    :param config_file  name of config file to retrieve
    :param logger       logger object to log messages during process

    create and verify config object based on config file input
    """

    logger.info('Config file location: ' + config_file)

    config = configparser.ConfigParser()

    # open config file to verify existence and return object
    try:
        config.read_file(open(config_file))
        config.read(config_file)
    except Exception as e:
        errmsg = 'Error loading Configuration file. . .'
        logger.critical(errmsg)
        logger.exception(e)
        raise ConfigLoadError(errmsg)

    return config


def get_config_value(config_obj, logger, section, key):
    """
    :param config_file  name of config file to retrieve
    :param logger       logger object to log messages during process
    :param section      name of section to retrieve
    :param key          name of key value to retrieve within section

    retrieve value for section/key from config object
    """

    # verify key exists before retrieving and returning value
    if config_obj.has_option(section, key):
        config_value = config_obj.get(section, key)
        return config_value
    else:
        errmsg = 'Config key ' + key + ' missing from section ' + section
        logger.critical(errmsg)
        raise ConfigKeyError(errmsg)
