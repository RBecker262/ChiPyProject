"""
updteam.py
Author: Robert Becker
Date: May 21, 2017
Purpose: use daily schedule to extract team data from gameday boxscore

Setup file/url names based on optional date arugment (mm-dd-yyyy), or use today
Load daily schedule dictionary into memory
Use schedule to search thru boxscore dictionaries to get all team info
Update teamMaster dictionary with any new team data found
Keep log of games played for each team and pointers to today's games
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
import myutils


# setup global variables
LOGGING_INI = 'backend_logging.ini'
CONFIG_INI = 'backend_config.ini'
DAILY_SCHEDULE = 'schedule_YYYYMMDD.json'
TEAM_MSTR_I = 'teamMaster.json'
TEAM_MSTR_O = 'teamMaster_YYYYMMDD.json'
BOXSCORE = 'http://gd2.mlb.com/_directory_/boxscore.json'


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
    -d or --date  optional, extract player stats for this date if provided
    -p of --path  optional, provides path of all ini files (must end with /)
    """

    parser = argparse.ArgumentParser('Command line arguments')
    parser.add_argument(
        '-d',
        '--date',
        help='Date of daily schedule for input - mm-dd-yyyy format',
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

    schedule_input = DAILY_SCHEDULE.replace('YYYYMMDD', yyyymmdd)
    team_output = TEAM_MSTR_O.replace('YYYYMMDD', yyyymmdd)

    return (schedule_input, team_output)


def load_daily_schedule(schedule_in):
    """
    :param schedule_in: filename for daily schedule file to load into memory

    daily schedule must exist to extract any info from boxscore dictionaries
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

    remove game related keys from master dictionary for each team in case
    teams don't play on a given date, keys are rebuilt for teams that do play
    """

    teamkeylist = list(masterdict)

    for teamkey in teamkeylist:
        teamdatakeys = list(masterdict[teamkey])
        if 'today_1' in teamdatakeys:
            del masterdict[teamkey]['today_1']
            del masterdict[teamkey]['today_1_time']
        if 'today_2' in teamdatakeys:
            del masterdict[teamkey]['today_2']
            del masterdict[teamkey]['today_2_time']
        if 'today_opp' in teamdatakeys:
            del masterdict[teamkey]['today_opp']

    return masterdict


def update_entry_for_game_1(sched_dict, mstr_dict, box_lev_3, homeaway, team):
    """
    :param sched_dict: schedule dictionary entry for given game
    :param mstr_dict:  current team master dictionary
    :param box_lev_3:  boxscore dictionary level 3 where team info resides
    :param homeaway:   identifies team as home or away
    :param team:       identifies team 3 character code

    create a complete updated team entry including team's schedule to date
    """

    game_dir = sched_dict['directory']
    gametime = sched_dict['game_time']
    teamname = sched_dict[homeaway + '_short']

    try:
        # grab team schedule from master and add current game
        sched = mstr_dict[team]['schedule']
        sched.update({box_lev_3['game_id']: game_dir})
    except Exception:
        # first time schedule being created for this team
        sched = {box_lev_3['game_id']: game_dir}

    # set opponent for today's game
    if homeaway == 'home':
        atvs = 'vs '
        oppkey = 'away'
    else:
        atvs = 'at '
        oppkey = 'home'

    # build team record (W-L) and opponent (at Chicago Cubs / vs Chicago Cubs)
    rec = box_lev_3[homeaway + '_wins'] + '-' + box_lev_3[homeaway + '_loss']
    opp = atvs + box_lev_3[oppkey + '_fname']

    # create complete entry for all team fields including updated team schedule
    entry = {team:
             {'club_name': box_lev_3[homeaway + '_fname'],
              'club_short': teamname,
              'record': rec,
              'today_home_away': homeaway,
              'today_1': game_dir,
              'today_1_time': gametime,
              'today_opp': opp,
              'schedule': sched}}

    return entry


def game_1_update(sched_dict, mstr_dict, box_lev_3, daily_team):
    """
    :param sched_dict: schedule dictionary entry for given game
    :param mstr_dict:  current team master dictionary
    :param box_lev_3:  boxscore dictionary level 3 where team info resides
    :param daily_team: complete dictionary entries for teams playing today

    create complete entries for home and away teams
    merge home and away entries into the daily team dictionary
    """

    home = sched_dict['home_code']
    away = sched_dict['away_code']

    # home team update for single game or 1st game of doubleheader
    home_entry = update_entry_for_game_1(sched_dict,
                                         mstr_dict,
                                         box_lev_3,
                                         'home',
                                         home)

    # away team update for single game or 1st game of doubleheader
    away_entry = update_entry_for_game_1(sched_dict,
                                         mstr_dict,
                                         box_lev_3,
                                         'away',
                                         away)

    # merge home and away entries into the today's team master
    daily_team.update(home_entry)
    daily_team.update(away_entry)

    return daily_team


def update_entry_for_game_2(sched_dict, box_lev_3, homeaway, daily_team):
    """
    :param sched_dict: schedule dictionary entry for given game
    :param box_lev_3:  boxscore dictionary level 3 where team info resides
    :param homeaway:   identifies team as home or away
    :param daily_team: dictionary entry for team to be update with game 2 info

    update entry created for game 1 of double header using data from game 2
    """

    game_dir = sched_dict['directory']
    gametime = sched_dict['game_time']

    # update the team record but opponent would be the same
    rec = box_lev_3[homeaway + '_wins'] + '-' + box_lev_3[homeaway + '_loss']

    upd_entry = {'record': rec,
                 'today_2': game_dir,
                 'today_2_time': gametime}
    daily_team.update(upd_entry)

    # add game 2 of double header to team schedule history
    upd_entry = {box_lev_3['game_id']: game_dir}
    daily_team['schedule'].update(upd_entry)

    return daily_team


def game_2_update(sched_dict, box_lev_3, daily_team):
    """
    :param sched_dict: schedule dictionary entry for given game
    :param box_lev_3:  boxscore dictionary level 3 where team info resides
    :param daily_team: complete dictionary entries for teams playing today

    create complete entries for home and away teams
    use home and away entries to update each team's entry in the daily master
    """

    # home team update for 2nd game of doubleheader
    home_entry = update_entry_for_game_2(sched_dict,
                                         box_lev_3,
                                         'home',
                                         daily_team[sched_dict['home_code']])

    # away team update for 2nd game of doubleheader
    away_entry = update_entry_for_game_2(sched_dict,
                                         box_lev_3,
                                         'away',
                                         daily_team[sched_dict['away_code']])

    # merge entries into today's master at team level as not all keys updated
    daily_team[sched_dict['home_code']].update(home_entry)
    daily_team[sched_dict['away_code']].update(away_entry)

    return daily_team


def load_boxscore(game_dir, game_id):
    """
    :param game_dir: MLB data server directory where game boxscore exists
    :param game_id:  unique ID given to each game of season by MLB

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
    :param sched_dict: daily schedule used to drive team extract process
    :param mstr_dict:  team master dictionary

    for each entry in daily schedule retrieve team info from game's boxscore
    and apply to daily master. handling double headers made this way fun!
    """

    # delete todays games in team master since we are rebuilding today
    # get list of game ids from schedule (key) and init todays daily master
    mstr_dict = reset_todays_games_in_master(mstr_dict)
    gameidlist = sorted(sched_dict.keys())
    daily_team_dict = {}

    # for each key, go to boxscore for that game and exctract all team data
    for key in gameidlist:

        # load boxscore dictionary for current game directory
        # if not found game was postponed so skip to next key (game id)
        try:
            box_level_3 = load_boxscore(sched_dict[key]['directory'], key)
        except LoadDictionaryError:
            continue

        if key.endswith('1'):
            # update home/away teams for single game or game 1 of doubleheader
            daily_team_dict = game_1_update(sched_dict[key],
                                            mstr_dict,
                                            box_level_3,
                                            daily_team_dict)

        elif key.endswith('2'):
            # use second game of doubleheader to update entry created by game 1
            daily_team_dict = game_2_update(sched_dict[key],
                                            box_level_3,
                                            daily_team_dict)

    # return newly updated master entries for all teams playing today
    return daily_team_dict


def invoke_updteam_as_sub(gamedate, arg_path):
    """
    :param gamedate: date of the games in format "MM-DD-YYYY"
    :param arg_path: path to ini files

    This routine is invoked when running as imported function vs main driver
    """

    rc = main(gamedate, arg_path)

    logger.info('Script as function completion code: ' + str(rc))

    return rc


def main(gamedate, arg_path):
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

    io = determine_filenames(gamedate)
    schedule_in = data_path + io[0]
    team_out = data_path + io[1]
    team_in = data_path + TEAM_MSTR_I

    # load daily schedule dictionary into memory, must exist or will bypass
    try:
        todays_schedule_dict = load_daily_schedule(schedule_in)
    except LoadDictionaryError:
        return 20

    # load team master dictionary into memory
    try:
        with open(team_in, 'r') as teamMaster:
            team_mstr_dict = json.load(teamMaster)
    # if no master build one from scratch
    except Exception:
        team_mstr_dict = {}

    logger.info('Creating team master file: ' + team_out)

    # use daily schedule to extract info from associated boxscore dictionaries
    todays_team_dict = process_schedule(todays_schedule_dict, team_mstr_dict)

    # update master dictionary variable and write to snapshot output file
    team_mstr_dict.update(todays_team_dict)

    with open(team_out, 'w') as teamfile:
        json.dump(team_mstr_dict, teamfile,
                  sort_keys=True, indent=4, ensure_ascii=False)

    # copy snapshot to master file name for ongoing updates through the season
    shutil.move(team_out, team_in)

    return 0


if __name__ == '__main__':

    args = get_command_arguments()

    cc = main(args.game_date, args.ini_path)

    logger.info('Script as main completion code: ' + str(cc))
    sys.exit(cc)
