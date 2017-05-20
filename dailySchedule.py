"""
dailySchedule.py
Author: Robert Becker
Date: May 13, 2017
Purpose: Parse the daily master scoreboard to extract MLB schedule for the day

Setup file/url names based on optional date arugment (mm-dd-yyyy), or today
Load master scoreboard dictionary into memory
Search thru dictionary to get directory information for all MLB games for date
Create output file with all schedules for the given date
"""


import sys
import argparse
import logging
import logging.config
import datetime
import json
import requests


# setup global variables
SCRIPT = 'dailySchedule.py'
LOGGING_INI = 'dailySchedule_logging.ini'
DAILY_SCHEDULE = 'Data/schedule_YYYYMMDD.json'
URL1 = 'http://gd2.mlb.com/components/game/mlb/year_YYYY'
URL2 = '/month_MM'
URL3 = '/day_DD'
URL4 = '/master_scoreboard.json'


class LoadDictionaryError(ValueError):
    pass


def init_logger():
    """
    initialize global variable logger and set script name
    """

    global logger
    logger = logging.getLogger(SCRIPT)


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
    logger.info('Command arguments: ' + str(argue.game_date))

    return argue


def determine_filenames(gamedate=None):
    """
    :param date: date of the games in format "MM-DD-YYYY"
    """

    if gamedate is not None:
        yyyy = gamedate[6:10]
        mm = gamedate[0:2]
        dd = gamedate[3:5]
    else:
        yyyy = datetime.date.today().strftime("%Y")
        mm = datetime.date.today().strftime("%m")
        dd = datetime.date.today().strftime("%d")

    mmddyyyy = mm + '-' + dd + '-' + yyyy
    urly = URL1.replace('YYYY', yyyy)
    urlm = URL2.replace('MM', mm)
    urld = URL3.replace('DD', dd)
    url_input = urly + urlm + urld + URL4

    sched_output = DAILY_SCHEDULE.replace('YYYYMMDD', yyyy + mm + dd)

    logger.info('Master Scoreboard dictionary location: ' + url_input)
    logger.info('Daily Schedule output file: ' + sched_output)

    return (url_input, sched_output, mmddyyyy)


def load_scoreboard_dictionary(scoreboardurl, gamedate):
    """
    :param scoreboardurl: url of json dictionary to load into memory
    :param gamedate:      date of MLB games used to extract schedules
    """

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
    As soon as game data is found return to previous recursion level
    """

    keylist = list(indict.keys())

    # if directory found, create entry in result dict and return to prev level
    if 'game_data_directory' in keylist:
        gcstart = len(indict['game_data_directory']) - 15
        gamecode = indict['game_data_directory'][gcstart:]
        entry = {gamecode:
                 {"directory": indict['game_data_directory'] + '/',
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


def invoke_dailySchedule_as_sub(gamedate=None):
    """
    :param gamedate: date of the games in format "MM-DD-YYYY"

    This routine is invoked when running as imported function vs main driver
    """

    init_logger()
    logger.info('Executing script dailySchedule.py as sub-function')
    rc = main(gamedate)

    return rc


def main(gamedate=None):

    # setup master scoreboard input and daily schedule output
    io = determine_filenames(gamedate)
    scoreboard_loc = io[0]
    schedule_out = io[1]
    date_of_games = io[2]

    # load master scoreboard dictionary into memory
    try:
        scoreboard_dict = load_scoreboard_dictionary(scoreboard_loc,
                                                     date_of_games)
    except LoadDictionaryError:
        return 20

    logger.info('Creating Daily Schedule file for date: ' + date_of_games)

    # initilize result and call function to search for team schedules
    resultdict = {}
    schedule_dict = search_dictionary(scoreboard_dict, resultdict)

    # write all games scheduled to daily schedule output file
    with open(schedule_out, 'w') as schedulefile:
        json.dump(schedule_dict, schedulefile,
                  sort_keys=True, indent=4, ensure_ascii=False)

    return 0


if __name__ == '__main__':
    logging.config.fileConfig(LOGGING_INI)
    init_logger()
    logger.info('Executing script as main function')

    args = get_command_arguments()

    cc = main(args.game_date)

    logger.info('Completion code: ' + str(cc))
    sys.exit(cc)
