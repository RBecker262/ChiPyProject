"""
playerMaster.py
Author: Robert Becker
Date: May 16, 2017
Purpose: use daily schedule to extract player data from gameday boxscore

Setup file/url names based on optional date arugment (mm-dd-yyyy), or today
Load daily schedule dictionary into memory
Use schedule to search thru boxscore dictionaries to get all player info
Update playerMaster dictionary with any new player data found
"""


import sys
import argparse
import logging
import logging.config
import datetime
import json
import requests


# setup global variables
SCRIPT = 'playerMaster.py'
LOGGING_INI = 'playerMaster_logging.ini'
DAILY_SCHEDULE = 'Data/schedule_YYYYMMDD.json'
PLAYER_MSTR_I = 'Data/playerMaster.json'
PLAYER_MSTR_O = 'Data/playerMaster_YYYYMMDD.json'
BOXSCORE = 'http://gd2.mlb.com/_directory_/boxscore.json'


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
    --date  optional, will extract players found in boxscore for this date
    """

    parser = argparse.ArgumentParser('playerMaster command line arguments')
    parser.add_argument(
        '-d',
        '--date',
        help='Date of daily schedule for input - mm-dd-yyyy format',
        dest='game_date',
        type=str)

    argue = parser.parse_args()
    logger.info('Command arguments: ' + str(argue.game_date))

    return argue


def determine_filenames(game_date=None):
    """
    :param date: date of the games in format "MM-DD-YYYY"
    """

    if game_date is not None:
        yyyy = game_date[6:10]
        mm = game_date[0:2]
        dd = game_date[3:5]
    else:
        yyyy = datetime.date.today().strftime("%Y")
        mm = datetime.date.today().strftime("%m")
        dd = datetime.date.today().strftime("%d")

    mmddyyyy = mm + '-' + dd + '-' + yyyy
    schedule_input = DAILY_SCHEDULE.replace('YYYYMMDD', yyyy + mm + dd)
    player_output = PLAYER_MSTR_O.replace('YYYYMMDD', yyyy + mm + dd)

    logger.info('dailySched dictionary location: ' + schedule_input)
    logger.info('Updated player dictionary location: ' + player_output)

    return (schedule_input, player_output, mmddyyyy)


def load_daily_schedule(schedule_in):
    """
    :param schedule_in: filename for daily schedule file to load into memory
    """

    logger.info('Loading dailySchedule dictionary')

    try:
        with open(schedule_in) as schedulefile:
            return json.load(schedulefile)
    except Exception as e:
        errmsg = 'Error loading dailySchedule dictionary. . .'
        logger.critical(errmsg)
        logger.exception(e)
        raise LoadDictionaryError(errmsg)


def process_schedule_entries(sched_dict):
    """
    :param sched_dict: daily schedule file used to drive player extract process
    """

    logger.info('Applying updates to player master dictionary')

    # get dailySchedule key list and start with blank result player dictionary
    keylist = list(sched_dict)
    daily_player_dict = {}

    # for each key, go to boxscore for that game and exctract all player data
    for key in keylist:

        boxscoreurl = BOXSCORE.replace('/_directory_/',
                                       sched_dict[key]["directory"])
        logger.info('Loading boxscore dictionary: ' + boxscoreurl)

        try:
            boxresp = requests.get(boxscoreurl)
            boxscore_dict = json.loads(boxresp.text)
        except Exception:
            errmsg = 'Boxscore dictionary not created yet for: ' + key
            logger.warning(errmsg)
            continue

        # set home and away team codess, init player result dict for this game
        home = sched_dict[key]["home_code"]
        away = sched_dict[key]["away_code"]
        resultdict = {}

        # search thru boxscore for current game and retrieve player data
        entry = search_dictionary(boxscore_dict, home, away, None, resultdict)

        # use single game player extract to update overall player result dict
        daily_player_dict.update(entry)

    return daily_player_dict


def search_dictionary(indict, hometeam, awayteam, team_code, resultdict):
    """
    :param indict:     dictionary to be parsed
    :param hometeam:   home team code starts as None and set once found in dict
    :param awayteam:   away team code starts as None and set once found in dict
    :param team_code:  set to hometeam or awayteam once team_flag is found
    :param resultdict: result dictionary, starts blank, updated for each entry

    Function loops through dictionary keys and examines values
    If function finds nested dictionary, call itself to parse next dict level
    If function finds list, call function to parse the next list level
    As soon as player data is found return result to previous recursion level
    """

    keylist = list(indict.keys())

    # save team codes to pass to lower dict levels where player data resides
    if 'team_flag' in keylist:
        if indict['team_flag'] == 'home':
            team_code = hometeam
        else:
            team_code = awayteam

    # if player found, create entry in result dict and return to previous level
    if 'name' in keylist:
        if indict['pos'] == 'P':
            position = 'P'
        else:
            position = 'B'
        entry = {indict['name']:
                 {'full_name': indict['name_display_first_last'],
                  'team_code': team_code,
                  'position': indict['pos'],
                  'point_pos': position}}
        resultdict.update(entry)
        logger.debug(indict['name'] + " added to player result dictionary")

        return resultdict

    # for each dictionary value call appropriate function based on type
    for dictkey in keylist:
        if isinstance(indict[dictkey], dict):
            resultdict = search_dictionary(indict[dictkey],
                                           hometeam,
                                           awayteam,
                                           team_code,
                                           resultdict)
        elif isinstance(indict[dictkey], list):
            resultdict = search_list(indict[dictkey],
                                     hometeam,
                                     awayteam,
                                     team_code,
                                     resultdict)

    # return whatever is in result dicionary at end of this dictionary level
    return resultdict


def search_list(inlist, hometeam, awayteam, team_code, resultdict):
    """
    :param indict:     dictionary to be parsed
    :param hometeam:   home team code starts as None and set once found in dict
    :param awayteam:   away team code starts as None and set once found in dict
    :param team_code:  set to hometeam or awayteam once team_flag is found
    :param resultdict: result dictionary, starts blank, updated for each entry

    If function finds nested dictionary, call function to parse next dict level
    If function finds list, call itself to parse the next list level
    """

    # for each list value call appropriate function based on type
    for listentry in inlist:
        if isinstance(listentry, dict):
            resultdict = search_dictionary(listentry,
                                           hometeam,
                                           awayteam,
                                           team_code,
                                           resultdict)
        elif isinstance(listentry, list):
            resultdict = search_list(listentry,
                                     hometeam,
                                     awayteam,
                                     team_code,
                                     resultdict)

    # return whatever is in result dicionary at end of this list
    return resultdict


def invoke_playerMaster_as_sub(gamedate=None):
    """
    :param gamedate: date of the games in format "MM-DD-YYYY"

    This routine is invoked when running as imported function vs main driver
    """

    init_logger()
    logger.info('Executing script playerMaster.py as sub-function')
    rc = main(gamedate)

    return rc


def main(gamedate=None):

    io = determine_filenames(gamedate)
    schedule_in = io[0]
    player_out = io[1]
    date_of_games = io[2]

    # load daily schedule dictionary into memory, must exist
    try:
        todays_schedule_dict = load_daily_schedule(schedule_in)
    except LoadDictionaryError:
        return 20

    logger.info('Creating Player Master file for date: ' + date_of_games)

    # use daily schedule to extract from each associated boxscore dictionary
    todays_player_dict = process_schedule_entries(todays_schedule_dict)

    # update player master dictionary with latest round of updates
    with open(PLAYER_MSTR_I, 'r') as playerMaster:
        player_mstr_dict = json.load(playerMaster)

    player_mstr_dict.update(todays_player_dict)

    with open(player_out, 'w') as playerfile:
        json.dump(player_mstr_dict, playerfile,
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
