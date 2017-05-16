"""
dailySched.py
Author: Robert Becker
Date: May 13, 2017
Purpose: Parse the daily master scoreboard to extract MLB schedule for the day

Read config file to get location of the master scoreboard
Load dictionary into memory
Call search_dictionary to get directory information for all MLB games today
"""


import sys
import argparse
import logging
import logging.config
import datetime
import json
import requests


# setup global variables
CONFIG_INI = 'dailySched_config.ini'
LOGGING_INI = 'dailySched_logging.ini'
DAILY_SCHEDULE = 'Data/schedule_YYYYMMDD.json'
URL1 = 'http://gd2.mlb.com/components/game/mlb/year_YYYY'
URL2 = '/month_MM'
URL3 = '/day_DD'
URL4 = '/master_scoreboard.json'

# setup logging and log initial message
logging.config.fileConfig(LOGGING_INI)
logger = logging.getLogger(__name__)
logger.info('Executing script: dailySched.py')


class LoadDictionaryError(ValueError):
    pass


def get_command_arguments():
    """
    --date  optional, will extract schedules for this date if provided
    """

    parser = argparse.ArgumentParser('Gameday schedule command line arguments')
    parser.add_argument(
        '-d',
        '--date',
        help='Date of daily schedule to build - mm-dd-yyyy format',
        dest='game_date',
        type=str)

    argue = parser.parse_args()
    logger.info('dailySched.py command arguments: ' + str(argue.game_date))

    return argue


def determine_filenames(arg):

    if arg.game_date:
        yyyy = arg.game_date[6:10]
        mm = arg.game_date[0:2]
        dd = arg.game_date[3:5]
    else:
        yyyy = datetime.date.today().strftime("%Y")
        mm = datetime.date.today().strftime("%m")
        dd = datetime.date.today().strftime("%d")

    urly = URL1.replace('YYYY', yyyy)
    urlm = URL2.replace('MM', mm)
    urld = URL3.replace('DD', dd)
    url_input = urly + urlm + urld + URL4

    sched_output = DAILY_SCHEDULE.replace('YYYYMMDD', yyyy + mm + dd)

    logger.info('Input dictionary location: ' + url_input)
    logger.info('Output file: ' + sched_output)

    return (url_input, sched_output)


def load_dictionary(jsonurl):

    try:
        jsonresp = requests.get(jsonurl)
        dictdata = json.loads(jsonresp.text)
        return dictdata
    except Exception as e:
        errmsg = 'Error loading dictionary from url. . .'
        logger.critical(errmsg)
        logger.exception(e)
        raise LoadDictionaryError(errmsg)


def search_dictionary(indict, resultdict):
    """
    Input parameters:
    indict     = dictionary to be parsed
    resultdict = result dictionary, starts blank and updated for each new entry

    Function loops through dictionary keys and examines values
    If function finds a nested dictionary, call itself to parse next level
    If function finds a list, call listlevel to parse the list
    As soon as game data is found return to previous recursion level
    """

    # get dictionary key list from and create entry in result dictionary
    keylist = list(indict.keys())

    if 'game_data_directory' in keylist:
        # print('Keys where GDD found...' + str(keylist))
        gcstart = len(indict['game_data_directory']) - 15
        gamecode = indict['game_data_directory'][gcstart:]
        entry = {gamecode:
                 {"directory": indict['game_data_directory'],
                  "away_code": indict['away_code'],
                  "home_code": indict['home_code']}}
        resultdict.update(entry)
        logger.debug(gamecode + " entry added to result dictionary")

        return resultdict

    # for each dictionary value call appropriate function based on type
    for dictkey in keylist:
        if isinstance(indict[dictkey], dict):
            resultdict = search_dictionary(indict[dictkey], resultdict)
        elif isinstance(indict[dictkey], list):
            resultdict = search_list(indict[dictkey], resultdict)

    # return whatever is in result dicionary at end of this dictionary level
    return resultdict


def search_list(inlist, resultdict):
    """
    Input parameters:
    inlist     = list to be parsed
    resultdict = result dictionary, starts blank and updated for each new entry

    Function loops through a list and examines list entries
    If function finds a nested dictionary, it calls dictlevel
    If function finds a list, it calls itself to parse the list
    """

    # for each list value call appropriate function based on type
    for listentry in inlist:
        if isinstance(listentry, dict):
            resultdict = search_dictionary(listentry, resultdict)
        elif isinstance(listentry, list):
            resultdict = search_list(listentry, resultdict)

    # return whatever is in result dicionary at end of this list
    return resultdict


def main():

    args = get_command_arguments()

    io = determine_filenames(args)
    jsonloc = io[0]
    schedule_out = io[1]

    # load json dictionary into memory
    try:
        jsondict = load_dictionary(jsonloc)
    except LoadDictionaryError:
        return 20

    # call function to search for team schedules
    logger.info('Searching scoreboard dictionary for MLB daily schedule')

    resultdict = {}
    schedule = search_dictionary(jsondict, resultdict)

    with open(schedule_out, 'w') as schedulefile:
        json.dump(schedule, schedulefile,
                  sort_keys=True, indent=4, ensure_ascii=False)

    return 0


if __name__ == '__main__':
    cc = main()
    logger.info('dailySched.py completion code: ' + str(cc))
    sys.exit(cc)
