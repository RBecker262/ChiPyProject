from flask import Flask, request
import requests
from flask_restful import Resource, Api
import json

API_SERVER = 'http://127.0.0.1:5001'
TEAM_MSTR_I = 'Data/teamMaster.json'
PLYR_MSTR_I = 'Data/playerMaster.json'

app = Flask(__name__)
api = Api(app)


def get_pitching_stats(plyr_data, key, team):

    if team is not None:
        short_club_name = team['club_short']
    else:
        short_club_name = ' '

    statkey = 'stats_pitching'

    pitching = {key:
                {"name": plyr_data['full_name'],
                 "team": short_club_name,
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

    if team is not None:
        short_club_name = team['club_short']
    else:
        short_club_name = ' '

    statkey = 'stats_batting'

    if plyr_data['pos_type'] == 'B' or plyr_data[statkey]['avg'] > '.000':
        batting = {key:
                   {"name": plyr_data['full_name'],
                    "team": short_club_name,
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


class All_Teams_API(Resource):
    def get(self):

        result = {}

        with open(TEAM_MSTR_I, 'r') as teamMaster:
            team_mstr = json.load(teamMaster)

        for key in team_mstr.keys():

            gameopp = ''
            gametime = ''
            if 'today_1_time' in team_mstr[key].keys():
                gameopp = team_mstr[key]['today_opp']
                gametime = team_mstr[key]['today_1_time']
            if 'today_2_time' in team_mstr[key].keys():
                gametime += " / " + team_mstr[key]['today_2_time']

            team = {team_mstr[key]['club_name']:
                    {"code": key,
                     "club": team_mstr[key]['club_name'],
                     "short": team_mstr[key]['club_short'],
                     "record": team_mstr[key]['record'],
                     "opponent": gameopp,
                     "time": gametime}}
            result.update(team)

        return result


class Team_Players_API(Resource):
    def get(self, teamcode):

        batters = {}
        pitchers = {}
        result = {}

        with open(PLYR_MSTR_I, 'r') as playerMaster:
            plyr_mstr = json.load(playerMaster)

        for key in plyr_mstr.keys():

            if plyr_mstr[key]['club_code'] == teamcode:

                if 'stats_batting' in plyr_mstr[key]:
                    plyr = get_batting_stats(plyr_mstr[key], key, None)
                    if plyr is not None:
                        batters.update(plyr)

                if 'stats_pitching' in plyr_mstr[key]:
                    plyr = get_pitching_stats(plyr_mstr[key], key, None)
                    pitchers.update(plyr)

        result = {"batters": batters, "pitchers": pitchers}

        return result


class Last_Name_API(Resource):
    def get(self, lastname):

        batters = {}
        pitchers = {}
        result = {}

        with open(PLYR_MSTR_I, 'r') as playerMaster:
            plyr_mstr = json.load(playerMaster)

        with open(TEAM_MSTR_I, 'r') as teamMaster:
            teams = json.load(teamMaster)

        for key in plyr_mstr.keys():

            stripkey = key.strip().lower()
            striplast = lastname.strip().lower()
            arglen = len(striplast)

            if stripkey[0:arglen] == striplast[0:arglen]:

                team = teams[plyr_mstr[key]['club_code']]

                if 'stats_batting' in plyr_mstr[key]:
                    plyr = get_batting_stats(plyr_mstr[key], key, team)
                    if plyr is not None:
                        batters.update(plyr)

                if 'stats_pitching' in plyr_mstr[key]:
                    plyr = get_pitching_stats(plyr_mstr[key], key, team)
                    pitchers.update(plyr)

        result = {"batters": batters, "pitchers": pitchers}

        return result


api.add_resource(All_Teams_API, '/allteams')
api.add_resource(Team_Players_API, '/teamplayers/<string:teamcode>')
api.add_resource(Last_Name_API, '/lastname/<string:lastname>')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)
