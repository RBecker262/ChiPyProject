"""
dailysched.py
Author: Robert Becker
Date: May 13, 2017
Purpose: Parse the daily master scoreboard to extract MLB schedule for the day

Setup file/url names based on optional date arugment (mm-dd-yyyy), or use today
Load master scoreboard dictionary into memory
Search thru dictionary to get directory information for all MLB games for date
Create output file with all schedules for the given date
"""


import sys
import os
import argparse
import logging
import logging.config
import datetime
import json
import requests
import myutils


# setup global variables
LOGGING_INI = 'backend_logging.ini'
CONFIG_INI = 'backend_config.ini'
DAILY_SCHEDULE = 'schedule_YYYYMMDD.json'
URL1 = 'http://gd2.mlb.com/components/game/mlb/year_YYYY'
URL2 = '/month_MM'
URL3 = '/day_DD'
URL4 = '/master_scoreboard.json'


class LoadDictionaryError(ValueError):
    pass


def init_logger(ini_path):
    """
    :param ini_path: path to ini files

    initialize global variable logger and setup log
    """

    global logger

    log_ini_file = ini_path + LOGGING_INI

    logging.config.fileConfig(log_ini_file, disable_existing_loggers=False)
    logger = logging.getLogger(os.path.basename(__file__))


def get_command_arguments():
    """
    -d or --date  optional, extract schedules for this date if provided
    -p of --path  optional, provides path of all ini files (must end with /)
    """

    parser = argparse.ArgumentParser('Gameday schedule command line arguments')
    parser.add_argument(
        '-d',
        '--date',
        help='Date of daily schedule to build - mm-dd-yyyy format',
        dest='game_date',
        type=str)
    parser.add_argument(
        '-p',
        '--path',
        help='Path for all ini files',
        dest='ini_path',
        type=str)

    argue = parser.parse_args()

    return argue


def determine_filenames(gamedate=None):
    """
    :param gamedate: date of the games in format "MM-DD-YYYY"

    gamedate is used throughout url and file names as guide to extracting data
    """

    # subtract 6 hours from today's date for games ending after midnight
    if gamedate is None:
        gamedate = datetime.datetime.today()
        gamedate += datetime.timedelta(hours=-11)
        gamedate = gamedate.strftime("%m-%d-%Y")

    yyyymmdd = gamedate[6:10] + gamedate[0:2] + gamedate[3:5]

    urly = URL1.replace('YYYY', gamedate[6:10])
    urlm = URL2.replace('MM', gamedate[0:2])
    urld = URL3.replace('DD', gamedate[3:5])
    url_input = urly + urlm + urld + URL4

    sched_output = DAILY_SCHEDULE.replace('YYYYMMDD', yyyymmdd)

    return (url_input, sched_output, gamedate)


def load_scoreboard_dictionary(scoreboardurl, gamedate):
    """
    :param scoreboardurl: url of json dictionary to load into memory
    :param gamedate:      date of MLB games used to extract schedules

    load the Master Scoreboard, it may not exist yet for current date
    """

    logger.info('Loading master scoreboard dictionary from: ' + scoreboardurl)

    try:
        scoreboardresp = requests.get(scoreboardurl)
        scoreboarddata = json.loads(scoreboardresp.text)
        return scoreboarddata
    except Exception:
        errmsg = 'Master Scoreboard dictionary not created for: ' + gamedate
        logger.warning(errmsg)
        raise LoadDictionaryError(errmsg)


def search_dictionary(indict, resultdict):
    """
    :param indict:     dictionary to be parsed
    :param resultdict: result dictionary, starts blank, updated for each entry

    Function loops through dictionary keys and examines values
    If function finds nested dictionary, call itself to parse next dict level
    If function finds list, call function to parse the next list level
    Once game data found capture data and return to previous recursion level
    """

    keylist = list(indict.keys())

    # if directory found, create entry in result dict and return to prev level
    if 'game_data_directory' in keylist:
        gcstart = len(indict['game_data_directory']) - 15
        gamecode = indict['game_data_directory'][gcstart:]

        entry = {gamecode:
                 {"directory": indict['game_data_directory'] + '/',
                  "away_code": indict['away_code'],
                  "away_short": indict['away_team_name'],
                  "home_code": indict['home_code'],
                  "home_short": indict['home_team_name'],
                  "game_time": indict['home_time'] + indict['home_ampm']}}

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
    :param inlist:     list to be parsed
    :param resultdict: result dictionary, starts blank, updated for each entry

    Function loops through a list and examines list entries

    If function finds nested dictionary, call function to parse next dict level
    If function finds list, call itself to parse the next list level
    """

    # for each list value call appropriate function based on type
    for listentry in inlist:
        if isinstance(listentry, dict):
            resultdict = search_dictionary(listentry, resultdict)
        elif isinstance(listentry, list):
            resultdict = search_list(listentry, resultdict)

    # return whatever is in result dicionary at end of this list
    return resultdict


def invoke_dailysched_as_sub(gamedate, arg_path):
    """
    :param gamedate: date of the games in format "MM-DD-YYYY"
    :param arg_path: path to ini files

    this routine is invoked when running as imported function vs main driver
    """

    rc = main(gamedate, arg_path)

    logger.info('Script as function completion code: ' + str(rc))

    return rc


def main(gamedate, arg_path):
    """
    :param gamedate: date of the games in format "MM-DD-YYYY"
    :param arg_path: path to ini files
    """

    if arg_path is None:
        ini_path = ''
    else:
        ini_path = arg_path

    init_logger(ini_path)

    # get the data directory from the config file
    try:
        section = "DirectoryPaths"
        key = "DataPath"
        config = myutils.load_config_file(ini_path + CONFIG_INI, logger)
        data_path = myutils.get_config_value(config, logger, section, key)
    except myutils.ConfigLoadError:
        return 1
    except myutils.ConfigKeyError:
        return 2

    # if the data directory does not exist then create it
    if not os.path.isdir(data_path):
        logger.info('Creating data directory: ' + data_path)
        os.mkdir(data_path)

    # setup master scoreboard input and daily schedule output
    io = determine_filenames(gamedate)
    scoreboard_loc = io[0]
    schedule_out = data_path + io[1]
    date_of_games = io[2]

    # load master scoreboard dictionary into memory
    try:
        scoreboard_dict = load_scoreboard_dictionary(scoreboard_loc,
                                                     date_of_games)
    except LoadDictionaryError:
        return 20

    logger.info('Creating daily schedule file: ' + schedule_out)

    # initilize result and call function to search for team schedules
    resultdict = {}
    schedule_dict = search_dictionary(scoreboard_dict, resultdict)

    # write all games scheduled to daily schedule output file
    with open(schedule_out, 'w') as schedulefile:
        json.dump(schedule_dict, schedulefile,
                  sort_keys=True, indent=4, ensure_ascii=False)

    return 0


if __name__ == '__main__':

    args = get_command_arguments()

    cc = main(args.game_date, args.ini_path)

    logger.info('Script as main completion code: ' + str(cc))
    sys.exit(cc)
