"""
updplayer.py
Author: Robert Becker
Date: May 16, 2017
Purpose: use daily schedule to extract player data from gameday boxscore

Setup file/url names based on optional date arugment (mm-dd-yyyy), or use today
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
import myutils


# setup global variables
LOGGING_INI = 'backend_logging.ini'
CONFIG_INI = 'backend_config.ini'
DAILY_SCHEDULE = 'schedule_YYYYMMDD.json'
PLAYER_MSTR_I = 'playerMaster.json'
PLAYER_MSTR_O = 'playerMaster_YYYYMMDD.json'
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
    player_output = PLAYER_MSTR_O.replace('YYYYMMDD', yyyymmdd)

    return (schedule_input, player_output)


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


def load_boxscore(game_dir, game_id):
    """
    :param game_dir: MLB data server directory where game boxscore exists
    :param game_id:  unique ID given to each game of season by MLB

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
    :param sched_dict: daily schedule used to drive player extract process

    for each entry in daily schedule, retrieve player info from that boxscore
    and apply to master. doubleheaders are not an issue for player update.
    daily_player_dict will hold all player updates to be made to master.
    """

    # get dailysched keys and start with blank player dictionary for today
    game_id_list = sorted(sched_dict.keys())
    daily_player_dict = {}

    # for each key, go to boxscore for that game and exctract all player data
    for key in game_id_list:

        # reset result dictionary to hold all player data from current game
        result = {}

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
                                  result,
                                  None)

        # merge player data from current game into today's player dictionary
        daily_player_dict.update(entry)

    # return newly updated master entries for all players playing today
    return daily_player_dict


def build_pitching_stats(indict):
    """
    :param indict:  boxscore dictionary from which to extract player data

    this is called when the pitching stats for one player is found
    extract all pitching data, create an entry and return it
    """

    keylist = list(indict.keys())

    # key used for nested dictionary within player entry for pitching stats
    statkey = 'stats_pitching'

    # set initial values in case given keys are not found in dictionary
    wins = 0
    so = 0
    era = 0
    walks = 0
    hits = 0
    ip = 0
    er = 0
    saves = 0

    # for each pitching stat found update the associated variable
    # can't convert era to float type when pitcher era is infinity
    if 'w' in keylist:
        wins = int(indict['w'])
    if 's_so' in keylist:
        so = int(indict['s_so'])
    if 'era' in keylist and '-' not in indict['era']:
        era = float(indict['era'])
    if 's_bb' in keylist:
        walks = int(indict['s_bb'])
    if 's_h' in keylist:
        hits = int(indict['s_h'])
    if 's_ip' in keylist:
        ip = float(indict['s_ip'])
    if 'er' in keylist:
        er = int(indict['s_er'])
    if 'sv' in keylist:
        saves = int(indict['sv'])

    pitcherstats = {'wins': wins,
                    'so': so,
                    'era': era,
                    'walks': walks,
                    'hits': hits,
                    'ip': ip,
                    'er': er,
                    'saves': saves}

    return (statkey, pitcherstats)


def build_batting_stats(indict):
    """
    :param indict:  boxscore dictionary from which to extract player data

    this is called when the batting stats for one player is found
    extract all batting data, create an entry and return it
    """

    keylist = list(indict.keys())

    # key used for nested dictionary within player entry for batting stats
    statkey = 'stats_batting'

    # set initial values in case given keys are not found in dictionary
    hits = 0
    walks = 0
    hr = 0
    rbi = 0
    runs = 0
    avg = '.000'

    # for each batting stat found update the associated variable
    # avg stays type string since no math will be done and format is consistent
    if 's_h' in keylist:
        hits = int(indict['s_h'])
    if 's_bb' in keylist:
        walks = int(indict['s_bb'])
    if 's_hr' in keylist:
        hr = int(indict['s_hr'])
    if 's_rbi' in keylist:
        rbi = int(indict['s_rbi'])
    if 's_r' in keylist:
        runs = int(indict['s_r'])
    if 'avg' in keylist:
        avg = indict['avg']

    batterstats = {'hits': hits,
                   'walks': walks,
                   'hr': hr,
                   'rbi': rbi,
                   'runs': runs,
                   'avg': avg}

    return (statkey, batterstats)


def build_player_stats(prevlev, indict):
    """
    :param prevlev: previous level, used to identify pitching vs batting stats
    :param indict:  boxscore dictionary from which to extract player data

    establish the position type for the player
    call appropriate routine to get pitching vs batting stats
    """

    if indict['pos'] == 'P':
        pos_type = 'P'
    else:
        pos_type = 'B'

    if prevlev == 'pitcher':
        pitcher = build_pitching_stats(indict)
        statkey = pitcher[0]
        playerstats = pitcher[1]

    elif prevlev == 'batter':
        batter = build_batting_stats(indict)
        statkey = batter[0]
        playerstats = batter[1]

    return (statkey, playerstats, pos_type)


def update_result_dict(indict, result, statkey, stats, teamcode, pos_type):
    """
    :param indict:   boxscore dictionary from which to extract player data
    :param result:   all dictionary entries being created from the current game
    :param statkey:  sub dictionary key to identify picther vs batter stats
    :param stats:    pitcher or batter stats for player found at current level
    :param teamcode: team code that player belongs to
    :param pos_type: P for pitcher or B for Batter

    called to create or update a player entry in result dictionary with stats
    some players have both pitching and batting stats (NL pitchers), but only
    one set of stats is updated at a time, hence the need to update entries
    """

    # if player already in result dictionary, update that entry with the
    # pitcher or batter stats just found, only one is found at a time
    if indict['name'] in list(result.keys()):
        logger.debug(indict['name'] + " updating player in master")
        result[indict['name']].update({statkey: stats})

    # name does not already exist so create new entry for player
    else:
        logger.debug(indict['name'] + " adding player to master")
        entry = {indict['name']:
                 {'full_name': indict['name_display_first_last'],
                  'club_code': teamcode,
                  'position': indict['pos'],
                  'pos_type': pos_type,
                  statkey: stats}}
        result.update(entry)

    return result


def search_dictionary(indict, hometeam, awayteam, teamcode, result, prevlev):
    """
    :param indict:   boxscore dictionary for current game
    :param hometeam: team code starts as None and set once found to pass deeper
    :param awayteam: team code starts as None and set once found to pass deeper
    :param teamcode: set to hometeam or awayteam once team_flag is found
    :param result:   result dictionary, starts blank, updated for each entry
    :param prevlev:  previous level key, used to identify pitchers vs batters

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

    # if player found, create entry in result and return to previous level
    if 'name' in keylist:
        player_stats = build_player_stats(prevlev,
                                          indict)
        statkey = player_stats[0]
        stats = player_stats[1]
        pos_type = player_stats[2]

        result = update_result_dict(indict,
                                    result,
                                    statkey,
                                    stats,
                                    teamcode,
                                    pos_type)

        return result

    # for each dictionary value call appropriate function based on type
    for dictkey in keylist:
        if isinstance(indict[dictkey], dict):
            result = search_dictionary(indict[dictkey],
                                       hometeam,
                                       awayteam,
                                       teamcode,
                                       result,
                                       dictkey)
        elif isinstance(indict[dictkey], list):
            result = search_list(indict[dictkey],
                                 hometeam,
                                 awayteam,
                                 teamcode,
                                 result,
                                 dictkey)

    # return whatever is in result dicionary at end of this dictionary level
    return result


def search_list(inlist, hometeam, awayteam, teamcode, result, prevlev):
    """
    :param indict:   list from boxscore dictionary to be parsed
    :param hometeam: team code starts as None and set once found to pass deeper
    :param awayteam: team code starts as None and set once found to pass deeper
    :param teamcode: set to hometeam or awayteam once team_flag is found
    :param result:   result dictionary, starts blank, updated for each entry
    :param prevlev:  previous level key, used to identify pitchers vs batters

    If function finds nested dictionary, call function to parse next dict level
    If function finds list, call itself to parse the next list level
    """

    # for each list value call appropriate function based on type
    for listentry in inlist:
        if isinstance(listentry, dict):
            result = search_dictionary(listentry,
                                       hometeam,
                                       awayteam,
                                       teamcode,
                                       result,
                                       prevlev)
        elif isinstance(listentry, list):
            result = search_list(listentry,
                                 hometeam,
                                 awayteam,
                                 teamcode,
                                 result,
                                 prevlev)

    # return whatever is in result dicionary at end of this list
    return result


def invoke_updplayer_as_sub(gamedate, arg_path):
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
    main process to update the player master
    determine file and url names based on date of games
    load the day's schedule into memory (possible there are no games for date)
    open current player master and load into memory
    call function to process the day's schedule, returns updates to master
    apply updates to player master dictionary, write to file with date in name
    use shell utility to copy new dictionary to player master file name
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
    player_out = data_path + io[1]
    player_in = data_path + PLAYER_MSTR_I

    # load daily schedule dictionary into memory, must exist or will bypass
    try:
        todays_schedule_dict = load_daily_schedule(schedule_in)
    except LoadDictionaryError:
        return 20

    # load player master dictionary into memory
    try:
        with open(player_in, 'r') as playerMaster:
            player_mstr_dict = json.load(playerMaster)
    # if no master build one from scratch
    except Exception:
        player_mstr_dict = {}

    logger.info('Creating player master file: ' + player_out)

    # use daily schedule to extract info from associated boxscore dictionaries
    todays_player_dict = process_schedule(todays_schedule_dict)

    # update master dictionary variable and write to snapshot output file
    player_mstr_dict.update(todays_player_dict)

    with open(player_out, 'w') as playerfile:
        json.dump(player_mstr_dict, playerfile,
                  sort_keys=True, indent=4, ensure_ascii=True)

    # copy snapshot to master file name for ongoing updates through the season
    shutil.move(player_out, player_in)

    return 0


if __name__ == '__main__':

    args = get_command_arguments()

    cc = main(args.game_date, args.ini_path)

    logger.info('Script as main completion code: ' + str(cc))
    sys.exit(cc)
