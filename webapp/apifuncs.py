"""
apifuncs.py
Author: Robert Becker
Date: July 2, 2017
Purpose: contains all functions used by the various API's of this website
"""

import requests
import json


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
    :param api_url: specific url used to get player stats (season or today)

    possible urls:  - /API_lastname/xxxxx   argument is partial last name
                    - /API_teamplayers/xxx  argument is team code
                    - /API_todaystats/xxxxx argument is player code
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
    :param team:      team master entry for player's team, or could be None

    formats the pitchers dictionary for player entry used in html form
    """

    # team is not passed if getting players by team, so blank out team name
    if team is not None:
        club_short = team['club_short']
    else:
        club_short = ' '

    statkey = 'stats_pitching'

    pitching = {key:
                {"name": plyr_data['full_name'],
                 "team": club_short,
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
    :param team:      team master entry for player's team, or could be None

    formats the batters dictionary for player entry used in html form
    """

    # team is not passed if getting players by team, so blank out team name
    if team is not None:
        club_short = team['club_short']
    else:
        club_short = ' '

    statkey = 'stats_batting'

    # take all batters (position players) or any pitcher who has batting data
    if plyr_data['pos_type'] == 'B' or plyr_data[statkey]['avg'] > '.000':
        batting = {key:
                   {"name": plyr_data['full_name'],
                    "team": club_short,
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
    :param homeaway:    vs = home, at = away
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

    if homeaway == 'vs':
        loc = 'home'
    else:
        loc = 'away'

    for x in range(0, 2):

        # match batting dictionary list item with player home or away value
        if batting[x]['team_flag'] == loc:
            for p in range(0, len(batting[x]['batter'])):
                if batting[x]['batter'][p]['name'] == playercode:
                    stats.update({"batting": batting[x]['batter'][p]})

        # match pitching dictionary list item with player home or away value
        if pitching[x]['team_flag'] == loc:
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

    # set initial values to have a basis for doing math
    bhits = 0
    bwalks = 0
    hr = 0
    rbi = 0
    runs = 0
    avg = 0

    # for each batting stat found update the associated variable
    # avg is field name in html but for todays stats will hold At Bats instead
    # column heading will reflect AVG or AB based on which stats are displayed
    if 'batting' in result1.keys():
        keylist = result1['batting'].keys()
        if 'h' in keylist:
            bhits += int(result1['batting']['h'])
        if 'bb' in keylist:
            bwalks += int(result1['batting']['bb'])
        if 'hr' in keylist:
            hr += int(result1['batting']['hr'])
        if 'rbi' in keylist:
            rbi += int(result1['batting']['rbi'])
        if 'r' in keylist:
            runs += int(result1['batting']['r'])
        if 'ab' in keylist:
            avg += int(result1['batting']['ab'])

    if 'batting' in result2.keys():
        keylist = result2['batting'].keys()
        if 'h' in keylist:
            bhits += int(result2['batting']['h'])
        if 'bb' in keylist:
            bwalks += int(result2['batting']['bb'])
        if 'hr' in keylist:
            hr += int(result2['batting']['hr'])
        if 'rbi' in keylist:
            rbi += int(result2['batting']['rbi'])
        if 'r' in keylist:
            runs += int(result2['batting']['r'])
        if 'ab' in keylist:
            avg += int(result2['batting']['ab'])

    # if all stats added together are at least 1 then player batted today
    # if all stats added together = 0 then he did not bat
    if (bhits + bwalks + hr + rbi + runs + avg) > 0:
        batting = {playercode:
                   {"name": fullname,
                    "team": clubname,
                    "pos": pos,
                    "avg": avg,
                    "hits": bhits,
                    "hr": hr,
                    "rbi": rbi,
                    "runs": runs,
                    "walks": bwalks,
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

    # set initial values to have a basis for doing math
    wins = 0
    so = 0
    era = 0
    pwalks = 0
    phits = 0
    ip = 0
    er = 0
    saves = 0

    # for each pitching stat found update the associated variable
    # innings pitched for today is counted as outs but will use same column
    # column heading will reflect Outs or IP based on which stats are displayed
    # era is calculated to 2 decimals based on outs and earned runs
    if 'pitching' in result1.keys():
        keylist = result1['pitching'].keys()
        if 'win' in keylist and result1['pitching']['win']:
            wins += 1
        if 'so' in keylist:
            so += int(result1['pitching']['so'])
        if 'bb' in keylist:
            pwalks += int(result1['pitching']['bb'])
        if 'h' in keylist:
            phits += int(result1['pitching']['h'])
        if 'out' in keylist:
            ip += int(result1['pitching']['out'])
        if 'er' in keylist:
            er += int(result1['pitching']['er'])
        if 'save' in keylist and result1['pitching']['save']:
            saves += 1
        if ip > 0:
            ert = (27 / ip) * er
            era = str("{:.2f}".format(ert))

    if 'pitching' in result2.keys():
        keylist = result2['pitching'].keys()
        if 'win' in keylist and result2['pitching']['win']:
            wins += 1
        if 'so' in keylist:
            so += int(result2['pitching']['so'])
        if 'bb' in keylist:
            pwalks += int(result2['pitching']['bb'])
        if 'h' in keylist:
            phits += int(result2['pitching']['h'])
        if 'out' in keylist:
            ip += int(result2['pitching']['out'])
        if 'er' in keylist:
            er += int(result2['pitching']['er'])
        if 'save' in keylist and result2['pitching']['save']:
            saves += 1
        if ip > 0:
            ert = (27 / ip) * er
            era = str("{:.2f}".format(ert))

    # if all stats added together are at least 1 then player pitched today
    # if all stats added together = 0 then he did not pitch
    if (wins + so + pwalks + phits + ip + er + saves) > 0:
        pitching = {playercode:
                    {"name": fullname,
                     "team": clubname,
                     "wins": wins,
                     "era": era,
                     "er": er,
                     "ip": ip,
                     "hits": phits,
                     "so": so,
                     "walks": pwalks,
                     "saves": saves,
                     "code": playercode}}
    else:
        pitching = {}

    return pitching
