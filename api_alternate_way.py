from flask import Flask
import json

apiapp = Flask(__name__)


@apiapp.route('/getteams')
def get_team_api():
    teams = {"Toronto Blue Jays":
             {"code": "tbj",
              "club": "Toronto Blue Jays",
              "record": "10-50",
              "opponent": "at Arizona Diamondbacks",
              "time": "3:00PM"},
             "Colorado Rockies":
             {"code": "col",
              "club": "Colorado Rockies",
              "record": "37-23",
              "opponent": "at Chicago Cubs",
              "time": "1:20PM"},
             "Chicago Cubs":
             {"code": "chn",
              "club": "Chicago Cubs",
              "record": "30-30",
              "opponent": "vs Colorado Rockies",
              "time": "1:20PM"}}

    resp = json.dumps(teams)
    return resp


if __name__ == '__main__':
    apiapp.run(host='127.0.0.1', port=5001)
