"""
teamMaster.py
Author: Robert Becker
Date: May 21, 2017
Purpose: use daily schedule to extract team data from gameday boxscore

Setup file/url names based on optional date arugment (mm-dd-yyyy), or today
Load daily schedule dictionary into memory
Use schedule to search thru boxscore dictionaries to get all team info
Update teamMaster dictionary with any new team data found
"""


import sys
import shutil
import argparse
import logging
import logging.config
import datetime
import json
import requests


# setup global variables
SCRIPT = 'teamMaster.py'
LOGGING_INI = 'teamMaster_logging.ini'
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
    logger = logging.getLogger(SCRIPT)


def get_command_arguments():
    """
    --date  optional, will extract teams found in boxscore for this date
    """

    parser = argparse.ArgumentParser('teamMaster command line arguments')
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

    if gamedate is not None:
        yyyy = gamedate[6:10]
        mm = gamedate[0:2]
        dd = gamedate[3:5]
    else:
        yyyy = datetime.date.today().strftime("%Y")
        mm = datetime.date.today().strftime("%m")
        dd = datetime.date.today().strftime("%d")

    mmddyyyy = mm + '-' + dd + '-' + yyyy
    schedule_input = DAILY_SCHEDULE.replace('YYYYMMDD', yyyy + mm + dd)
    team_output = TEAM_MSTR_O.replace('YYYYMMDD', yyyy + mm + dd)

    logger.info('dailySched dictionary location: ' + schedule_input)
    logger.info('Updated team dictionary location: ' + team_output)

    return (schedule_input, team_output, mmddyyyy)


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


def reset_todays_games_in_master(masterdict):

    keylist = list(masterdict)
    for key in keylist:
        keys = list(masterdict[key])
        if 'today_1' in keys:
            del masterdict[key]['today_1']
        if 'today_2' in keys:
            del masterdict[key]['today_2']

    return masterdict


def process_schedule(sched_dict, mstr_dict):
    """
    :param sched_dict: daily schedule file used to drive team extract process
    """

    mstr_dict = reset_todays_games_in_master(mstr_dict)

    logger.info('Applying updates to team master dictionary')

    # get dailySchedule key list and start with blank result team dictionary
    keylist = list(sched_dict)
    daily_team_dict = {}

    # for each key, go to boxscore for that game and exctract all team data
    for key in keylist:

        boxscoreurl = BOXSCORE.replace('/_directory_/',
                                       sched_dict[key]['directory'])
        logger.info('Loading boxscore dictionary: ' + boxscoreurl)

        try:
            boxresp = requests.get(boxscoreurl)
            boxscore_dict = json.loads(boxresp.text)
            box_level_3 = boxscore_dict['data']['boxscore']
        except Exception:
            errmsg = 'Boxscore dictionary not created yet for: ' + key
            logger.warning(errmsg)
            continue

        # set home and away team codess, init team result dict for this game
        home = sched_dict[key]['home_code']
        away = sched_dict[key]['away_code']

        # single game or first game of a double header
        if key[-1:] == '1':
            try:
                hist = mstr_dict[home]['game_hist']
                hist.update({box_level_3['game_id']:
                             sched_dict[key]['directory']})
            except Exception:
                hist = {box_level_3['game_id']: sched_dict[key]['directory']}

            entry = {home:
                     {'team_name': box_level_3['home_fname'],
                      'wins': box_level_3['home_wins'],
                      'losses': box_level_3['home_loss'],
                      'today_1': sched_dict[key]['directory'],
                      'game_hist': hist}}

            daily_team_dict.update(entry)

            try:
                hist = mstr_dict[away]['game_hist']
                hist.update({box_level_3['game_id']:
                             sched_dict[key]['directory']})
            except Exception:
                hist = {box_level_3['game_id']: sched_dict[key]['directory']}

            entry = {away:
                     {'team_name': box_level_3['away_fname'],
                      'wins': box_level_3['away_wins'],
                      'losses': box_level_3['away_loss'],
                      'today_1': sched_dict[key]['directory'],
                      'game_hist': hist}}

            daily_team_dict.update(entry)

        # definitely a double header
        elif key[-1:] == '2':
            upd_entry = {'wins': box_level_3['home_wins'],
                         'losses': box_level_3['home_loss'],
                         'today_2': sched_dict[key]['directory']}
            daily_team_dict[home].update(upd_entry)

            upd_entry = {box_level_3['game_id']: sched_dict[key]['directory']}
            daily_team_dict[home]['game_hist'].update(upd_entry)

            upd_entry = {'wins': box_level_3['away_wins'],
                         'losses': box_level_3['away_loss'],
                         'today_2': sched_dict[key]['directory']}
            daily_team_dict[away].update(upd_entry)

            upd_entry = {box_level_3['game_id']: sched_dict[key]['directory']}
            daily_team_dict[away]['game_hist'].update(upd_entry)

    return daily_team_dict


def invoke_teamMaster_as_sub(gamedate=None):
    """
    :param gamedate: date of the games in format "MM-DD-YYYY"

    This routine is invoked when running as imported function vs main driver
    """

    init_logger()
    logger.info('Executing script teamMaster.py as sub-function')
    rc = main(gamedate)

    return rc


def main(gamedate=None):

    io = determine_filenames(gamedate)
    schedule_in = io[0]
    team_out = io[1]
    date_of_games = io[2]

    # load daily schedule dictionary into memory, must exist
    try:
        todays_schedule_dict = load_daily_schedule(schedule_in)
    except LoadDictionaryError:
        return 20

    logger.info('Creating Team Master file for date: ' + date_of_games)

    # update team master dictionary with latest round of updates
    with open(TEAM_MSTR_I, 'r') as teamMaster:
        team_mstr_dict = json.load(teamMaster)

    # use daily schedule to extract from each associated boxscore dictionary
    todays_team_dict = process_schedule(todays_schedule_dict, team_mstr_dict)

    team_mstr_dict.update(todays_team_dict)

    with open(team_out, 'w') as teamfile:
        json.dump(team_mstr_dict, teamfile,
                  sort_keys=True, indent=4, ensure_ascii=False)

    shutil.copy(team_out, TEAM_MSTR_I)

    return 0


if __name__ == '__main__':
    logging.config.fileConfig(LOGGING_INI)
    init_logger()
    logger.info('Executing script as main function')

    args = get_command_arguments()

    cc = main(args.game_date)

    logger.info('Completion code: ' + str(cc))
    sys.exit(cc)
