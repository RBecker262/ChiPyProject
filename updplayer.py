"""
updplayer.py
Author: Robert Becker
Date: May 16, 2017
Purpose: use daily schedule to extract player data from gameday boxscore

Setup file/url names based on optional date arugment (mm-dd-yyyy), or today
Load daily schedule dictionary into memory
Use schedule to search thru boxscore dictionaries to get all player info
Update playerMaster dictionary with any new player data found
"""


import sys
import os
import shutil
import argparse
import logging
import logging.config
import datetime
import json
import requests


# setup global variables
LOGGING_INI = 'updplayer_logging.ini'
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
    logger = logging.getLogger(os.path.basename(__file__))


def get_command_arguments():
    """
    --date  optional, will extract players found in boxscore for this date
    """

    parser = argparse.ArgumentParser('Command line arguments')
    parser.add_argument(
        '-d',
        '--date',
        help='Date of daily schedule for input - mm-dd-yyyy format',
        dest='game_date',
        type=str)

    argue = parser.parse_args()
    logger.info('Command arguments: ' + str(argue.game_date))

    return argue


def determine_filenames(gamedate=None):
    """
    :param game_date: date of the games in format "MM-DD-YYYY"
    """

    if gamedate is None:
        gamedate = str(datetime.date.today())

    yyyymmdd = gamedate[6:10] + gamedate[0:2] + gamedate[3:5]

    schedule_input = DAILY_SCHEDULE.replace('YYYYMMDD', yyyymmdd)
    player_output = PLAYER_MSTR_O.replace('YYYYMMDD', yyyymmdd)

    return (schedule_input, player_output)


def load_daily_schedule(schedule_in):
    """
    :param schedule_in: filename for daily schedule file to load into memory
    """

    logger.info('Loading daily schedule from: ' + schedule_in)

    try:
        with open(schedule_in) as schedulefile:
            return json.load(schedulefile)
    except Exception as e:
        errmsg = 'Error loading dailySchedule dictionary. . .'
        logger.critical(errmsg)
        logger.exception(e)
        raise LoadDictionaryError(errmsg)


def load_boxscore(game_dir, game_id):
    """
    :param game_dir: MLB data server directory where game boxscore exists
    :param game_id:  unique ID given to game by MLB

    load the boxscore for a given game and return the entire dictionary
    """

    # load the boxscore dictionary based on current game directory
    boxscoreurl = BOXSCORE.replace('/_directory_/', game_dir)
    logger.info('Loading boxscore dictionary: ' + boxscoreurl)

    try:
        boxresp = requests.get(boxscoreurl)
        boxscore_dict = json.loads(boxresp.text)
    except Exception:
        errmsg = 'Boxscore dictionary not created yet for: ' + game_id
        logger.warning(errmsg)
        raise LoadDictionaryError(errmsg)

    return boxscore_dict


def process_schedule(sched_dict):
    """
    :param sched_dict: daily schedule file used to drive player extract process

    for each entry in the day's schedule, retrieve player info from the game's
    boxscore and apply to the master. doubleheaders not an issue for player
    """

    # get dailysched keys and start with blank player dictionary for today
    keylist = list(sched_dict)
    daily_player_dict = {}

    # for each key, go to boxscore for that game and exctract all player data
    for key in keylist:

        # reset result dictionary to hold all player data from current game
        resultdict = {}

        # load boxscore dictionary for current game directory
        # if not found game was postponed so skip to next key (game id)
        try:
            boxscore_dict = load_boxscore(sched_dict[key]['directory'], key)
        except LoadDictionaryError:
            continue

        # search thru boxscore for current game and retrieve all player data
        entry = search_dictionary(boxscore_dict,
                                  sched_dict[key]['home_code'],
                                  sched_dict[key]['away_code'],
                                  None,
                                  resultdict)

        # merge player data from current game into today's player dictionary
        daily_player_dict.update(entry)

    # return newly updated master entries for all players playing today
    return daily_player_dict


def search_dictionary(indict, hometeam, awayteam, teamcode, resultdict):
    """
    :param indict:     dictionary to be parsed
    :param hometeam:   home team code starts as None and set once found in dict
    :param awayteam:   away team code starts as None and set once found in dict
    :param teamcode:   set to hometeam or awayteam once team_flag is found
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
            teamcode = hometeam
        else:
            teamcode = awayteam

    # if player found, create entry in resultdict and return to previous level
    if 'name' in keylist:
        if indict['pos'] == 'P':
            position = 'P'
        else:
            position = 'B'
        entry = {indict['name']:
                 {'full_name': indict['name_display_first_last'],
                  'team_code': teamcode,
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
                                           teamcode,
                                           resultdict)
        elif isinstance(indict[dictkey], list):
            resultdict = search_list(indict[dictkey],
                                     hometeam,
                                     awayteam,
                                     teamcode,
                                     resultdict)

    # return whatever is in result dicionary at end of this dictionary level
    return resultdict


def search_list(inlist, hometeam, awayteam, teamcode, resultdict):
    """
    :param indict:     dictionary to be parsed
    :param hometeam:   home team code starts as None and set once found in dict
    :param awayteam:   away team code starts as None and set once found in dict
    :param teamcode:   set to hometeam or awayteam once team_flag is found
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
                                           teamcode,
                                           resultdict)
        elif isinstance(listentry, list):
            resultdict = search_list(listentry,
                                     hometeam,
                                     awayteam,
                                     teamcode,
                                     resultdict)

    # return whatever is in result dicionary at end of this list
    return resultdict


def invoke_updplayer_as_sub(gamedate=None):
    """
    :param gamedate: date of the games in format "MM-DD-YYYY"

    This routine is invoked when running as imported function vs main driver
    """

    init_logger()
    logger.info('Executing script as sub-function')
    rc = main(gamedate)

    logger.info('Script completion code: ' + str(rc))

    return rc


def main(gamedate=None):
    """
    main process to update the player master
    determine file and url names based on date of games
    load the day's schedule into memory (possible there are no games for date)
    open current player master and load into memory
    call function to process the day's schedule, returns updates to master
    apply updates to player master dictionary, write to file with date in name
    use shell utility to copy new dictionary to player master file name
    - this gives us a new master after each udpate and a snapshot at end of day
    """

    io = determine_filenames(gamedate)
    schedule_in = io[0]
    player_out = io[1]

    # load daily schedule dictionary into memory, must exist or will bypass
    try:
        todays_schedule_dict = load_daily_schedule(schedule_in)
    except LoadDictionaryError:
        return 20

    # load player master dictionary into memory
    try:
        with open(PLAYER_MSTR_I, 'r') as playerMaster:
            player_mstr_dict = json.load(playerMaster)
    except Exception:
        player_mstr_dict = {"-file": "Player Master Dictionary File"}

    logger.info('Creating player master file: ' + player_out)

    # use daily schedule to extract info from associated boxscore dictionaries
    todays_player_dict = process_schedule(todays_schedule_dict)

    # update master dictionary variable and write to snapshot output file
    player_mstr_dict.update(todays_player_dict)

    with open(player_out, 'w') as playerfile:
        json.dump(player_mstr_dict, playerfile,
                  sort_keys=True, indent=4, ensure_ascii=False)

    # copy snapshot to master file name for ongoing updates through the season
    shutil.copy(player_out, PLAYER_MSTR_I)

    return 0


if __name__ == '__main__':
    logging.config.fileConfig(LOGGING_INI)
    init_logger()
    logger.info('Executing script as main function')

    args = get_command_arguments()

    cc = main(args.game_date)

    logger.info('Script completion code: ' + str(cc))
    sys.exit(cc)