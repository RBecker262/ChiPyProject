"""
playerTeam.py
Author: Robert Becker
Date: May 16, 2017
Purpose: use daily schedule to extract player and team data from boxscore

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
LOGGING_INI = 'playerTeam_logging.ini'
DAILY_SCHEDULE = 'Data/schedule_YYYYMMDD.json'
PLAYER_MSTR_I = 'Data/playerMaster.json'
PLAYER_MSTR_O = 'Data/playerMaster_YYYYMMDD.json'
TEAM_MSTR_I = 'Data/teamMaster.json'
TEAM_MSTR_O = 'Data/teamMaster_YYYYMMDD.json'
WEBSITE = 'http://gd2.mlb.com'
BOXSCORE = '/boxscore.json'


# setup logging and log initial message
logging.config.fileConfig(LOGGING_INI)
logger = logging.getLogger(__name__)
logger.info('Executing script: teamPlayer.py')


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
        help='Date of daily schedule for input - mm-dd-yyyy format',
        dest='game_date',
        type=str)

    argue = parser.parse_args()
    logger.info('teamPlayer.py command arguments: ' + str(argue.game_date))

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

    schedule_input = DAILY_SCHEDULE.replace('YYYYMMDD', yyyy + mm + dd)
    player_output = PLAYER_MSTR_O.replace('YYYYMMDD', yyyy + mm + dd)
    team_output = TEAM_MSTR_O.replace('YYYYMMDD', yyyy + mm + dd)

    logger.info('Input dailySched dictionary location: ' + schedule_input)
    logger.info('Output player master file: ' + player_output)
    logger.info('Output team master file: ' + team_output)

    return (schedule_input, player_output, team_output)


def load_daily_schedule(schedule_in):

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

    keylist = list(sched_dict)
    daily_player_dict = {}

    for key in keylist:

        boxscoreurl = WEBSITE + sched_dict[key]["directory"] + BOXSCORE
        logger.info('Loading daily boxscore dictionary from: ' + boxscoreurl)

        try:
            boxresp = requests.get(boxscoreurl)
            boxscore_dict = json.loads(boxresp.text)
        except Exception as e:
            errmsg = 'Error loading boxscore dictionary. . .'
            logger.critical(errmsg)
            logger.exception(e)
            raise LoadDictionaryError(errmsg)

        home = sched_dict[key]["home_code"]
        away = sched_dict[key]["away_code"]
        resultdict = {}

        entry = search_dictionary(boxscore_dict, home, away, None, resultdict)

        daily_player_dict.update(entry)

    return daily_player_dict


def search_dictionary(indict, hometeam, awayteam, team_code, resultdict):
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

    if 'team_flag' in keylist:
        if indict['team_flag'] == 'home':
            team_code = hometeam
        else:
            team_code = awayteam

    if 'name' in keylist:
        # print('Keys where GDD found...' + str(keylist))
        if indict['pos'] == 'P':
            position = 'P'
        else:
            position = 'B'
        entry = {indict['name']:
                 {'team_code': team_code,
                  'position': indict['pos'],
                  'point_pos': position,
                  'full_name': indict['name_display_first_last']}}
        resultdict.update(entry)
        logger.debug(indict['name'] + " entry added to result dictionary")

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


def main():

    args = get_command_arguments()

    io = determine_filenames(args)
    schedule_in = io[0]
    player_out = io[1]
    # team_out = io[2]

    # load daily schedule dictionary into memory
    try:
        schedule_dict = load_daily_schedule(schedule_in)
    except LoadDictionaryError:
        return 20

    # use daily schedule to extract from each associated boxscore dictionary
    try:
        team_master_dict = process_schedule_entries(schedule_dict)
    except LoadDictionaryError:
        return 21

    with open(PLAYER_MSTR_I, 'r') as playerMaster:
        player_mstr_dict = json.load(playerMaster)

    player_mstr_dict.update(team_master_dict)

    with open(player_out, 'w') as playerfile:
        json.dump(player_mstr_dict, playerfile,
                  sort_keys=True, indent=4, ensure_ascii=False)

    return 0


if __name__ == '__main__':
    cc = main()
    logger.info('teamPlayer.py completion code: ' + str(cc))
    sys.exit(cc)
