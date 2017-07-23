"""
apifuncs.py
Author: Robert Becker
Date: July 2, 2017
Purpose: contains all functions used by the various API's of this website
"""

import requests
import json
import collections


class LoadDictionaryError(ValueError):
    pass


def load_dictionary_from_url(dict_url):
    """
    :param dict_url: url of online dictionary to be loaded

    try loading dictionary and return to caller, raise error if any issue
    """

    try:
        dictresp = requests.get(dict_url)
        dictload = json.loads(dictresp.text)
    except Exception:
        errmsg = 'Dictionary not available'
        raise LoadDictionaryError(errmsg)

    return dictload


def get_player_stats(api_url):
    """
    :param api_url: specific url used to get player stats (season only)

    API's using this function:
    /api/v1/players/team/xxxxx          argument is team code
    /api/v1/players/lastname/xxxxx      argument is partial last name
    /api/v1/boxscore/player/xxxxx       argument is player code
    """

    # make API call using url passed to function and load dictionary result
    api_resp = requests.get(api_url)
    api_str = api_resp.content.decode()
    loaded = json.loads(api_str)

    # start with empty result lists and load info into tables sorting on key
    batters = []
    pitchers = []
    for key in sorted(loaded['batters'].keys()):
        batters.append(loaded['batters'][key])
    for key in sorted(loaded['pitchers'].keys()):
        pitchers.append(loaded['pitchers'][key])

    return (batters, pitchers)


def get_pitching_stats(plyr_data, key, team):
    """
    :param plyr_data: player entry from player master file
    :param key:       player key used in result dictionary
    :param team:      team master entry for player's team

    formats the pitchers dictionary for player entry used in html form
    """

    statkey = 'stats_pitching'

    pitching = {key:
                {"name": plyr_data['full_name'],
                 "team": team['club_short'],
                 "wins": plyr_data[statkey]['wins'],
                 "era": str("{:.2f}".format(plyr_data[statkey]['era'])),
                 "er": plyr_data[statkey]['er'],
                 "ip": plyr_data[statkey]['ip'],
                 "hits": plyr_data[statkey]['hits'],
                 "so": plyr_data[statkey]['so'],
                 "walks": plyr_data[statkey]['walks'],
                 "saves": plyr_data[statkey]['saves'],
                 "code": key}}

    return pitching


def get_batting_stats(plyr_data, key, team):
    """
    :param plyr_data: player entry from player master file
    :param key:       player key used in result dictionary
    :param team:      team master entry for player's team

    formats the batters dictionary for player entry used in html form
    """

    statkey = 'stats_batting'

    # take all batters (position players) or any pitcher who has batting data
    if plyr_data['pos_type'] == 'B' or plyr_data[statkey]['avg'] > '.000':
        batting = {key:
                   {"name": plyr_data['full_name'],
                    "team": team['club_short'],
                    "pos": plyr_data['position'],
                    "avg": plyr_data[statkey]['avg'],
                    "hits": plyr_data[statkey]['hits'],
                    "hr": plyr_data[statkey]['hr'],
                    "rbi": plyr_data[statkey]['rbi'],
                    "runs": plyr_data[statkey]['runs'],
                    "walks": plyr_data[statkey]['walks'],
                    "code": key}}
    else:
        batting = None

    return batting


def get_today_stats(box_url, homeaway, playercode):
    """
    :param box_url:     MLB url of boxscore for this game to get player data
    :param homeaway:    indicates if team is 'home' or 'away'
    :param playercode:  player code to find within boxscore

    load boxscore dictionary then loop thru pitching and batting sections
    boxscore may not be available yet which is valid, so return empty result
    determine if player's team is home or away today
    find him in batting and/or pitching subdictionaries and save stats
    """

    stats = {}

    try:
        box_dict = load_dictionary_from_url(box_url)
        batting = box_dict['data']['boxscore']['batting']
        pitching = box_dict['data']['boxscore']['pitching']
    except Exception:
        return stats

    for x in range(0, 2):

        # match batting dictionary list item with player home or away value
        if batting[x]['team_flag'] == homeaway:
            for p in range(0, len(batting[x]['batter'])):
                if batting[x]['batter'][p]['name'] == playercode:
                    stats.update({"batting": batting[x]['batter'][p]})

        # match pitching dictionary list item with player home or away value
        if pitching[x]['team_flag'] == homeaway:
            if isinstance(pitching[x]['pitcher'], dict):
                if pitching[x]['pitcher']['name'] == playercode:
                    stats.update({"pitching": pitching[x]['pitcher']})
            else:
                for p in range(0, len(pitching[x]['pitcher'])):
                    if pitching[x]['pitcher'][p]['name'] == playercode:
                        stats.update({"pitching": pitching[x]['pitcher'][p]})

    return stats


def add_todays_results(result1, result2, playercode, fullname, pos, clubname):
    """
    :param result1:    player stats from game1 (if he played)
    :param result2:    player stats from game2 (if he played)
    :param playercode: player key to player master
    :param fullname:   player full name
    :param pos:        position played
    :param clubname:   team short name

    add stats from each game, player might have data in both, neither or just 1
    player might have hitting or pitching stats, or both, or neither, by game
    """

    batting = add_todays_batting(result1,
                                 result2,
                                 playercode,
                                 fullname,
                                 pos,
                                 clubname)

    pitching = add_todays_pitching(result1,
                                   result2,
                                   playercode,
                                   fullname,
                                   clubname)

    result = {"batters": batting, "pitchers": pitching}

    return result


def collate_stats(stats, day_stats, stat_trans, stat_type):
    """
    :param stats:      player stats entry from MLB boxscore for a game
    :param day_stats:  accumulated stats for a day to which to add
    :param stat_trans: translates MLB stat keys to Rob's stat keys
    :param stat_type:  indicates 'batting' or 'pitching'

    add a player-game stats to a running total for a day
    """

    for statkey in stat_trans.keys():
        if statkey in stats[stat_type].keys():
            if stats[stat_type][statkey] == 'true':
                day_stats[stat_trans[statkey]] += 1
            else:
                day_stats[stat_trans[statkey]] += int(
                    stats[stat_type][statkey])
    return day_stats


def add_todays_batting(result1, result2, playercode, fullname, pos, clubname):
    """
    :param result1:    player stats from game1 (if he played)
    :param result2:    player stats from game2 (if he played)
    :param playercode: player key to player master
    :param fullname:   player full name
    :param pos:        position played
    :param clubname:   team short name

    add stats from each game, player might have data in both, neither or just 1
    """

    # establish stat translation table from MLB's stat keys to Rob's stat keys
    bat_translation = {
        'h': 'bhits',
        'bb': 'bwalks',
        'hr': 'hr',
        'rbi': 'rbi',
        'r': 'runs',
        'ab': 'avg'
    }

    # set initial values to have a basis for doing math
    game_stats = {}
    for stat in bat_translation.keys():
        game_stats[bat_translation[stat]] = 0

    # for each batting stat found update the associated variable
    # avg is field name in html but for todays stats will hold At Bats instead
    # column heading will reflect AVG or AB based on which stats are displayed
    if 'batting' in result1.keys():
        game_stats = collate_stats(result1,
                                   game_stats,
                                   bat_translation,
                                   'batting')
    if 'batting' in result2.keys():
        game_stats = collate_stats(result2,
                                   game_stats,
                                   bat_translation,
                                   'batting')

    # if all stats added together are at least 1 then player batted today
    # if all stats added together = 0 then he did not bat
    allstats = collections.Counter(game_stats)
    if sum(allstats.values()) > 0:
        batting = {playercode:
                   {"name": fullname,
                    "team": clubname,
                    "pos": pos,
                    "avg": game_stats['avg'],
                    "hits": game_stats['bhits'],
                    "hr": game_stats['hr'],
                    "rbi": game_stats['rbi'],
                    "runs": game_stats['runs'],
                    "walks": game_stats['bwalks'],
                    "code": playercode}}
    else:
        batting = {}

    return batting


def add_todays_pitching(result1, result2, playercode, fullname, clubname):
    """
    :param result1:    player stats from game1 (if he played)
    :param result2:    player stats from game2 (if he played)
    :param playercode: player key to player master
    :param fullname:   player full name
    :param clubname:   team short name

    add stats from each game, player might have data in both, neither or just 1
    """

    # establish stat translation table from MLB's stat keys to Rob's stat keys
    pitch_translation = {
        'win': 'wins',
        'so': 'so',
        'bb': 'pwalks',
        'h': 'phits',
        'out': 'ip',
        'er': 'er',
        'save': 'saves',
    }

    # set initial values to have a basis for doing math
    game_stats = {}
    for stat in pitch_translation.keys():
        game_stats[pitch_translation[stat]] = 0

    # for each pitching stat found update the associated variable
    # wins and saves are boolean variables so if true 1 will be added to total
    # innings pitched for today is counted as outs but will use same column
    # column heading will reflect Outs or IP based on which stats are displayed
    # era is calculated to 2 decimals based on outs and earned runs
    if 'pitching' in result1.keys():
        game_stats = collate_stats(result1,
                                   game_stats,
                                   pitch_translation,
                                   'pitching')
    if 'pitching' in result2.keys():
        game_stats = collate_stats(result2,
                                   game_stats,
                                   pitch_translation,
                                   'pitching')

    if game_stats['ip'] > 0:
        ert = (27 / game_stats['ip']) * game_stats['er']
        era = str("{:.2f}".format(ert))

    # if all stats added together are at least 1 then player pitched today
    # if all stats added together = 0 then he did not pitch
    allstats = collections.Counter(game_stats)
    if sum(allstats.values()) > 0:
        pitching = {playercode:
                    {"name": fullname,
                     "team": clubname,
                     "wins": game_stats['wins'],
                     "era": era,
                     "er": game_stats['er'],
                     "ip": game_stats['ip'],
                     "hits": game_stats['phits'],
                     "so": game_stats['so'],
                     "walks": game_stats['pwalks'],
                     "saves": game_stats['saves'],
                     "code": playercode}}
    else:
        pitching = {}

    return pitching
