"""
updteam.py
Author: Robert Becker
Date: May 21, 2017
Purpose: use daily schedule to extract team data from gameday boxscore

Setup file/url names based on optional date arugment (mm-dd-yyyy), or today
Load daily schedule dictionary into memory
Use schedule to search thru boxscore dictionaries to get all team info
Update teamMaster dictionary with any new team data found
Keep history of all games each team plays and pointers to today's games
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
LOGGING_INI = 'updteam_logging.ini'
DAILY_SCHEDULE = 'Data/schedule_YYYYMMDD.json'
TEAM_MSTR_I = 'Data/teamMaster.json'
TEAM_MSTR_O = 'Data/teamMaster_YYYYMMDD.json'
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
    --date  optional, will extract team data found in boxscore for this date
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

    gamedate is used to determine filenames and url links
    since it is optional, today's date is used if gamedate not provided
    """

    if gamedate is None:
        gamedate = str(datetime.date.today())

    yyyymmdd = gamedate[6:10] + gamedate[0:2] + gamedate[3:5]

    schedule_input = DAILY_SCHEDULE.replace('YYYYMMDD', yyyymmdd)
    team_output = TEAM_MSTR_O.replace('YYYYMMDD', yyyymmdd)

    return (schedule_input, team_output)


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


def reset_todays_games_in_master(masterdict):
    """
    :param masterdict: team master dictionary to be updated

    remove today_1 & today_2 keys from master dictionary for each team in case
    teams don't play on a given date, keys are rebuilt for teams that do play
    """

    teamkeylist = list(masterdict)

    for teamkey in teamkeylist:
        teamdatakeys = list(masterdict[teamkey])
        if 'today_1' in teamdatakeys:
            del masterdict[teamkey]['today_1']
        if 'today_2' in teamdatakeys:
            del masterdict[teamkey]['today_2']

    return masterdict


def update_entry_for_game_1(game_dir, mstr_dict, box_lev_3, homeaway, team):
    """
    :param game_dir:    game directory for given date
    :param mstr_dict:   current team master dictionary
    :param box_level_3: boxscore dictionary level 3 where team info resides
    :param homeaway:    identifies team as home or away
    :param team:        identifies team 3 character code

    creates a complete updated entry per team including all game history
    """

    try:
        # grab team game history from master and add current game
        hist = mstr_dict[team]['game_hist']
        hist.update({box_lev_3['game_id']: game_dir})
    except Exception:
        # first time game history being created for this team
        hist = {box_lev_3['game_id']: game_dir}

    # create complete entry for all team fields including updated game history
    entry = {team:
             {'team_name': box_lev_3[homeaway + '_fname'],
              'wins': box_lev_3[homeaway + '_wins'],
              'losses': box_lev_3[homeaway + '_loss'],
              'today_1': game_dir,
              'game_hist': hist}}

    return entry


def game_1_update(game_dir, mstr_dict, box_lev_3, home, away, daily_team):
    """
    :param game_dir:   game directory for given date
    :param mstr_dict:  current team master dictionary
    :param box_lev_3:  boxscore dictionary level 3 where team info resides
    :param home:       identifies home team 3 character code
    :param away:       identifies away team 3 character code
    :param daily_team: complete dictionary entries for teams playing today

    create complete entries for home and away teams
    merge home and away entries into the daily team dictionary
    """

    # home team update for single game or 1st game of doubleheader
    home_entry = update_entry_for_game_1(game_dir,
                                         mstr_dict,
                                         box_lev_3,
                                         'home',
                                         home)

    # away team update for single game or 1st game of doubleheader
    away_entry = update_entry_for_game_1(game_dir,
                                         mstr_dict,
                                         box_lev_3,
                                         'away',
                                         away)

    # metge home and away entries into the today's team master
    daily_team.update(home_entry)
    daily_team.update(away_entry)

    return daily_team


def update_entry_for_game_2(game_dir, box_level_3, homeaway, daily_team):
    """
    :param game_dir:    game directory for given date
    :param box_level_3: boxscore dictionary level 3 where team info resides
    :param homeaway:    identifies team as home or away
    :param daily_team:  dictionary entry for team to be update with game 2 info

    complete updated team entry already created for game 1 of a double header
    this updates that team entry with data from game 2 of the double header
    """

    upd_entry = {'wins': box_level_3[homeaway + '_wins'],
                 'losses': box_level_3[homeaway + '_loss'],
                 'today_2': game_dir}
    daily_team.update(upd_entry)

    upd_entry = {box_level_3['game_id']: game_dir}
    daily_team['game_hist'].update(upd_entry)

    return daily_team


def game_2_update(game_dir, box_lev_3, home, away, daily_team):
    """
    :param game_dir:   game directory for given date
    :param box_lev_3:  boxscore dictionary level 3 where team info resides
    :param home:       identifies home team 3 character code
    :param away:       identifies away team 3 character code
    :param daily_team: complete dictionary entries for teams playing today

    create complete entries for home and away teams
    use home and away entries to update each team's entry in the master
    """

    # home team update for 2nd game of doubleheader
    home_entry = update_entry_for_game_2(game_dir,
                                         box_lev_3,
                                         'home',
                                         daily_team[home])

    # away team update for 2nd game of doubleheader
    away_entry = update_entry_for_game_2(game_dir,
                                         box_lev_3,
                                         'away',
                                         daily_team[away])

    # metge entries into today's master at team level as not all keys updated
    daily_team[home].update(home_entry)
    daily_team[away].update(away_entry)

    return daily_team


def load_boxscore(game_dir, game_id):
    """
    :param game_dir: MLB data server directory where game boxscore exists
    :param game_id:  unique ID given to game by MLB

    load the boxscore for a given game and return the entire 3rd level
    dictionary entry using key ['data']['directory'] as this contains
    the most current team information desired to keep in the team master
    """

    # load the boxscore dictionary based on current game directory
    boxscoreurl = BOXSCORE.replace('/_directory_/', game_dir)
    logger.info('Loading boxscore dictionary: ' + boxscoreurl)

    try:
        boxresp = requests.get(boxscoreurl)
        boxscore_dict = json.loads(boxresp.text)
        box_lev_3 = boxscore_dict['data']['boxscore']
    except Exception:
        errmsg = 'Boxscore dictionary not created yet for: ' + game_id
        logger.warning(errmsg)
        raise LoadDictionaryError(errmsg)

    return box_lev_3


def process_schedule(sched_dict, mstr_dict):
    """
    :param sched_dict: daily schedule file used to drive team extract process
    :param mstr_dict:  team master file to be updated through this process

    for each entry in the day's schedule, retrieve team info from the game's
    boxscore and apply to the master. handling double headers made this way fun
    """

    # delete todays games in team master since we are rebuilding today
    # get list of game ids from schedule (key) and init todays team master
    mstr_dict = reset_todays_games_in_master(mstr_dict)
    keylist = list(sched_dict)
    daily_team_dict = {}

    # for each key, go to boxscore for that game and exctract all team data
    for key in keylist:

        # load boxscore dictionary for current game directory
        # if not found game was postponed so skip to next key (game id)
        try:
            box_level_3 = load_boxscore(sched_dict[key]['directory'], key)
        except LoadDictionaryError:
            continue

        if key.endswith('1'):
            # update home/away teams for single game or game 1 of doubleheader
            daily_team_dict = game_1_update(sched_dict[key]['directory'],
                                            mstr_dict,
                                            box_level_3,
                                            sched_dict[key]['home_code'],
                                            sched_dict[key]['away_code'],
                                            daily_team_dict)

        elif key.endswith('2'):
            # use second game of doubleheader to update entry created by game 1
            daily_team_dict = game_2_update(sched_dict[key]['directory'],
                                            box_level_3,
                                            sched_dict[key]['home_code'],
                                            sched_dict[key]['away_code'],
                                            daily_team_dict)

    # return newly updated master entries for all teams playing today
    return daily_team_dict


def invoke_updteam_as_sub(gamedate=None):
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
    main process to update the team master
    determine file and url names based on date of games
    load the day's schedule into memory (possible there are no games for date)
    open current team master and load into memory
    call function to process the day's schedule, returns updates to master
    apply updates to team master dictionary, write to file with date in name
    use shell utility to copy new dictionary to team master file name
    - this gives us a new master after each udpate and a snapshot at end of day
    """

    io = determine_filenames(gamedate)
    schedule_in = io[0]
    team_out = io[1]

    # load daily schedule dictionary into memory, must exist or will bypass
    try:
        todays_schedule_dict = load_daily_schedule(schedule_in)
    except LoadDictionaryError:
        return 20

    # load team master dictionary into memory
    try:
        with open(TEAM_MSTR_I, 'r') as teamMaster:
            team_mstr_dict = json.load(teamMaster)
    except Exception:
        team_mstr_dict = {"-file": "Team Master Dictionary File"}

    logger.info('Creating team master file: ' + team_out)

    # use daily schedule to extract info from associated boxscore dictionaries
    todays_team_dict = process_schedule(todays_schedule_dict, team_mstr_dict)

    # update master dictionary variable and write to snapshot output file
    team_mstr_dict.update(todays_team_dict)

    with open(team_out, 'w') as teamfile:
        json.dump(team_mstr_dict, teamfile,
                  sort_keys=True, indent=4, ensure_ascii=False)

    # copy snapshot to master file name for ongoing updates through the season
    shutil.copy(team_out, TEAM_MSTR_I)

    return 0


if __name__ == '__main__':
    logging.config.fileConfig(LOGGING_INI)
    init_logger()
    logger.info('Executing script as main function')

    args = get_command_arguments()

    cc = main(args.game_date)

    logger.info('Script completion code: ' + str(cc))
    sys.exit(cc)
