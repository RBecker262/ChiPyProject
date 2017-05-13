"""
JSON Dictionary Parsing Program
Author: Robert Becker
Date: April 17, 2017
Purpose: Parse a JSON dictionary and return player info or print all data
Uses: JSON and requests libraries, response, and 2 recursive functions

Get Command Line arguments to determine data source and player stats desired
Read config file to get possible locations of a json dictionary (url or file)
Load dictionary from location (determined by Command Line arguments)
Call dictlevel function to begin parsing process

Config file can have many locations defined. Order of entries is irrelevant.
Example:
url=http://somewebsite.com/somedirectory/somefile.json
url1=http://somewebsite.com/somedirectory/someothefile.json
file1=../DataFiles/somelocalfile.json
file2=../DataFiles/anotherlocalfile.json
"""


import sys
import configparser
import logging
import logging.config
import json
import requests
import dictsrch


# set logging, config, and output file locations
CONFIG_INI = 'teamdata_config.ini'
LOGGING_INI = 'teamdata_logging.ini'

# setup logging and log initial message
logging.config.fileConfig(LOGGING_INI)
logger = logging.getLogger(__name__)
logger.info('Executing script: teamdata.py')


class ConfigLoadError(ValueError):
    pass


class JsonKeyMissingError(ValueError):
    pass


class LoadDictionaryError(ValueError):
    pass


def get_config_file(config_loc):

    logger.info('Config file location = ' + config_loc)

    config = configparser.ConfigParser()

    # open config file to verify existence, then read and return
    try:
        config.read_file(open(config_loc))
        config.read(config_loc)
        return config
    except Exception as e:
        errmsg = 'Error loading Configuration file. . .'
        logger.critical(errmsg)
        logger.exception(e)
        raise ConfigLoadError(errmsg)


def get_json_location(config):

    # verify input key is in DataSource before setting source location
    if config.has_option("DataSources", "url"):
        return config.get("DataSources", "url")
    else:
        errmsg = 'url key missing from config DataSource'
        logger.critical(errmsg)
        raise JsonKeyMissingError(errmsg)


def load_dictionary(jsonurl):

    # log dictionary location
    logger.info('Loading dictionary from location: ' + jsonurl)

    try:
        jsonresp = requests.get(jsonurl)
        dictdata = json.loads(jsonresp.text)
        return dictdata
    except Exception as e:
        errmsg = 'Error loading dictionary from url. . .'
        logger.critical(errmsg)
        logger.exception(e)
        raise LoadDictionaryError(errmsg)


def print_team_info(teamdict):

    # get list of dictionary keys from returned player data
    keylist = list(teamdict.keys())

    # print heading for player followed by his boxscore data
    for dictkey in keylist:
        print(dictkey + " = " + str(teamdict[dictkey]))


def main():

    # load config file into memory
    try:
        configdata = get_config_file(CONFIG_INI)
    except ConfigLoadError:
        return 1

    # get json dictionary information from config file
    try:
        jsonloc = get_json_location(configdata)
    except JsonKeyMissingError:
        return 10

    # load json dictionary into memory
    try:
        jsondict = load_dictionary(jsonloc)
    except LoadDictionaryError:
        return 20

    # call function to extract player data from dictionary and print it
    logger.info('Searching dictionary for today''schedules')

    schedules = dictsrch.search_dictionary(jsondict)

    print_team_info(schedules)

    return 0


if __name__ == '__main__':
    cc = main()
    logger.info('parsdict.py completion code: ' + str(cc))
    sys.exit(cc)
