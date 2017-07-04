"""
apifuncs.py
Author: Robert Becker
Date: July 2, 2017
Purpose: contains all functions used by the various API's of this website
"""

import requests
import json


def get_season_stats(api_url):
    """
    :param api_url: specific url used to get player stats

    possible urls:  - /API_lastname/xxxxx   argument is partial last name
                    - /API_teamplayers/xxx  argument is team code
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
                 "era": plyr_data[statkey]['era'],
                 "er": int(plyr_data[statkey]['er']),
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
