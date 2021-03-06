from flask import render_template, redirect, flash, request, url_for
import requests
import json
from webapp import webapp
from .forms import HomeForm, AboutForm, ByLastNameForm, ByTeamForm
from .forms import PlayerStatsForm, WatchListForm, VanAllanEffectForm
from webapp import apifuncs

DATA_FOLDER = '/usr/tmp/data/'
TEAM_MSTR_I = DATA_FOLDER + 'teamMaster.json'
PLYR_MSTR_I = DATA_FOLDER + 'playerMaster.json'
BOXSCORE = 'http://gd2.mlb.com/_directory_/boxscore.json'
API_SERVER = 'http://thesandlot-env.aquapjmcqz.us-east-2.elasticbeanstalk.com'


@webapp.route('/')
@webapp.route('/index')
@webapp.route('/TheSandlot')
def thesandlot():
    """
    display Home page
    """

    form = HomeForm()
    flash("Welcome to Rob's Sandlot!")
    return render_template("base.html",
                           title='Home',
                           form=form,
                           errors=False,
                           dispflash=True)


@webapp.route('/ByTeam', methods=['GET', 'POST'])
def byteam():
    """
    Search By Teams was clicked to display all teams, or a team was selected
    """

    form = ByTeamForm()

    # team had to be clicked from team list, redirect to playerstats
    if form.teamcode.data is not None:
        return redirect(url_for('playerstats', teamcode=form.teamcode.data))

    # make API call to retrieve all team information and display
    url = API_SERVER + '/api/v1/teams'
    api_resp = requests.get(url)
    api_str = api_resp.content.decode()
    loaded = json.loads(api_str)

    # load teams dictionary entries into list sorted on teamcode (team key)
    teams = []
    for key in sorted(loaded.keys()):
        teams.append(loaded[key])

    flash('Click on row to view team roster / stats')
    return render_template("byteam.html",
                           form=form,
                           teams=teams,
                           errors=False,
                           dispflash=True)


@webapp.route('/ByLastName', methods=['GET', 'POST'])
def bylastname():
    """
    Search By Last Name was clicked to display players who match the partial
    last name entered, or a partial name was entered and user clicked Submit
    """

    form = ByLastNameForm()

    # get lastname from form and set errors to false
    # errors controls green font for normal message and red for error message
    lastname = form.lastname.data
    errors = False

    # if POST check for len of argument > 0, if true redirect to playerstats
    # if POST and len of argument = 0 then user didn't enter anything
    if request.method == 'POST':
        if len(lastname.strip()) > 0:
            return redirect(url_for('playerstats',
                                    lastname=lastname,
                                    displastname=True))
        # user didn't enter anything in lastname field so highlight in red
        else:
            errors = True

    flash('Enter at least 1 letter of player last name:')
    return render_template("base.html",
                           form=form,
                           displastname=True,
                           errors=errors,
                           dispflash=True)


@webapp.route('/PlayerStats', methods=['GET', 'POST'])
def playerstats(teamcode=None, lastname=None, displastname=False):
    """
    :param teamcode:     code of team for displaying all players for team
    :param lastname:     partial name for displaying players by name search
    :param displastname: used in HTML to control display of Last Name field

    this handles all possible ways of displaying player stats, season and today
    season stats display by clicking on a team or entering partial last name
    if coming here from search by team the Last Name field is not displayed
    if coming here from search by last name then Last Name field is displayed
    boolean variable errors controls font color to use for any flash messages
       - errors = False: green for happy normal messages
       - errors = True:  red for error messages or when no results found
    """

    form = PlayerStatsForm()
    errors = False

    # get possible arguments passed to this routine
    teamcode = request.args.get('teamcode')
    lastname = request.args.get('lastname')
    playercode = form.playercode.data

    # set column headings for batting average and innings pitched
    # when displaying today's stats these will change to AB and Outs
    avg_ab = 'AVG'
    ip_outs = 'IP'

    if request.method == "GET" and teamcode:
        # request to display all players for team, call teamplayers api
        url = API_SERVER + '/api/v1/players/team/' + teamcode
        list = apifuncs.get_player_stats(url)
        batters = list[0]
        pitchers = list[1]
        form.displastname.data = displastname
        flash("Season stats displayed, toggle player row for today's stats")

    elif request.method == "GET" and lastname:
        # request to display players matching partial name, call lastname api
        # first get displastname argument, move it and lastname to form fields
        displastname = request.args.get('displastname')
        form.displastname.data = displastname
        form.lastname.data = lastname
        url = API_SERVER + '/api/v1/players/lastname/' + lastname
        list = apifuncs.get_player_stats(url)
        batters = list[0]
        pitchers = list[1]
        flash("Season stats displayed, toggle player row for today's stats")

    elif playercode is not None and str(playercode).strip() != '':
        # user clicked on player row, call todays stats api
        # get displastname from form since at this point we don't know if we
        # came here from search by team or search by last name
        # if from search by last name keep the last name field displayed
        # if from search by team do not display the last name field
        displastname = form.displastname.data
        if displastname is not None:
            lastname = form.lastname.data
        url = API_SERVER + '/api/v1/boxscore/player/' + playercode
        list = apifuncs.get_player_stats(url)
        batters = list[0]
        pitchers = list[1]
        avg_ab = 'AB'
        ip_outs = 'Outs'
        form.playercode.data = playercode
        if len(batters) == 0 and len(pitchers) == 0:
            flashmsg = playercode + ' has not played yet today'
            errors = True
        else:
            flashmsg = 'Stats from games played today'
        flash(flashmsg)

    else:
        # partial name field updated, if valid (len > 0) call lastname api
        displastname = form.displastname.data
        lastname = form.lastname.data
        if request.method == 'POST' and len(lastname.strip()) > 0:
            url = API_SERVER + '/api/v1/players/lastname/' + lastname
            list = apifuncs.get_player_stats(url)
            batters = list[0]
            pitchers = list[1]
            msg = "Season stats displayed, toggle player row for today's stats"
            flash(msg)
        else:
            batters = []
            pitchers = []
            errors = True
            flash('Enter at least 1 letter of player last name:')

    return render_template("playerstats.html",
                           form=form,
                           playercode=playercode,
                           batters=batters,
                           pitchers=pitchers,
                           displastname=displastname,
                           errors=errors,
                           avgab=avg_ab,
                           ipouts=ip_outs,
                           dispflash=True)


@webapp.route('/WatchList')
def watchlist():
    """
    display Watch List page
    """

    form = WatchListForm()
    flash('View and update the Watch List')
    return render_template("watchlist.html",
                           form=form,
                           displastname=False,
                           errors=False,
                           dispflash=True)


@webapp.route('/VanAllanEffect')
def vanallaneffect():
    """
    display VanAllanEffect page
    """

    form = VanAllanEffectForm()
    flash('SAVE THE CARDINALS!')
    return render_template("vanallaneffect.html",
                           form=form,
                           displastname=False,
                           errors=True,
                           dispflash=True)


@webapp.route('/About')
def about():
    """
    display About page
    """

    form = AboutForm()
    return render_template("about.html",
                           form=form,
                           displastname=False,
                           errors=False,
                           dispflash=False)

###############################################################################
#
#         A          PPPPPPPPP      IIIIIIIIIIII
#        AAA         PP       PP         II
#       AA AA        PP        PP        II
#      AA   AA       PP       PP         II           S  E  C  T  I  O  N
#     AAAAAAAAA      PPPPPPPPP           II           ===================
#    AA       AA     PP                  II
#   AA         AA    PP                  II
#  AA           AA   PP             IIIIIIIIIIII
#
###############################################################################


@webapp.route('/api/v1/teams', methods=['GET'])
def api_v1_teams():
    """
    retrieves info for all teams with opponents ant times for today's games
    """

    result = {}

    with open(TEAM_MSTR_I, 'r') as teamMaster:
        team_mstr = json.load(teamMaster)

    for key in team_mstr.keys():

        # establish opponent and time of game (or game 1 of double header)
        gameopp = ''
        gametime = ''
        if 'today_1_time' in team_mstr[key].keys():
            gameopp = team_mstr[key]['today_opp']
            gametime = team_mstr[key]['today_1_time']

        # display times of both games if playing a double header
        if 'today_2_time' in team_mstr[key].keys():
            gametime += " / " + team_mstr[key]['today_2_time']

        # result will include all teams whether they play today or not
        team = {team_mstr[key]['club_name']:
                {"code": key,
                 "club": team_mstr[key]['club_name'],
                 "short": team_mstr[key]['club_short'],
                 "record": team_mstr[key]['record'],
                 "opponent": gameopp,
                 "time": gametime}}
        result.update(team)

    # convert dictionary result to a string and return
    result_str = json.dumps(result)
    return result_str


@webapp.route('/api/v1/players/team/<string:teamcode>', methods=['GET'])
def api_v1_players_team(teamcode):
    """
    :param teamcode: team for which to display player season stats

    retrieves season stats for all players for the specified team
    """

    batters = {}
    pitchers = {}
    result = {}

    with open(PLYR_MSTR_I, 'r') as playerMaster:
        plyr_mstr = json.load(playerMaster)

    with open(TEAM_MSTR_I, 'r') as teamMaster:
        teams = json.load(teamMaster)

    # examine club code for every player to see if it matches team selected
    for key in plyr_mstr.keys():

        if plyr_mstr[key]['club_code'] == teamcode:

            # grab team entry for player's team
            team = teams[plyr_mstr[key]['club_code']]

            # player on team selected so see if he has batting statistics
            if 'stats_batting' in plyr_mstr[key]:
                plyr = apifuncs.get_batting_stats(plyr_mstr[key], key, team)

                # update is conditional for pitcher, must have batting stat > 0
                if plyr is not None:
                    batters.update(plyr)

            # player on team selected so see if he has pitching statistics
            if 'stats_pitching' in plyr_mstr[key]:
                plyr = apifuncs.get_pitching_stats(plyr_mstr[key], key, team)
                pitchers.update(plyr)

    # create dictionary result with a section for each, batters and pitchers
    result = {"batters": batters, "pitchers": pitchers}

    # convert dictionary result to a string and return
    result_str = json.dumps(result)
    return result_str


@webapp.route('/api/v1/players/lastname/<string:lastname>', methods=['GET'])
def api_v1_players_lastname(lastname):
    """
    :param lastname: partial last name of player

    retrieves season stats for all players who match partial last name entered
    """

    batters = {}
    pitchers = {}
    result = {}

    with open(PLYR_MSTR_I, 'r') as playerMaster:
        plyr_mstr = json.load(playerMaster)

    with open(TEAM_MSTR_I, 'r') as teamMaster:
        teams = json.load(teamMaster)

    # examine all player keys (last name) in master file
    for key in plyr_mstr.keys():

        # strip trailing spaces and convert all chars to lower for both the
        # last name entered and last name on file, save len of argument
        stripkey = key.strip().lower()
        striplast = lastname.strip().lower()
        arglen = len(striplast)

        # compare argument and last name up to number of letters entered
        if stripkey[0:arglen] == striplast[0:arglen]:

            # grab team entry for player's team
            team = teams[plyr_mstr[key]['club_code']]

            # player name matches argument so see if he has batting statistics
            if 'stats_batting' in plyr_mstr[key]:
                plyr = apifuncs.get_batting_stats(plyr_mstr[key], key, team)

                # update is conditional for pitcher, must have batting stat > 0
                if plyr is not None:
                    batters.update(plyr)

            # player name matches argument so see if he has pitching statistics
            if 'stats_pitching' in plyr_mstr[key]:
                plyr = apifuncs.get_pitching_stats(plyr_mstr[key], key, team)
                pitchers.update(plyr)

    # create dictionary result with a section for each, batters and pitchers
    result = {"batters": batters, "pitchers": pitchers}

    # convert dictionary result to a string and return
    result_str = json.dumps(result)
    return result_str


@webapp.route('/api/v1/boxscore/player/<string:playercode>', methods=['GET'])
def api_v1_boxscore_player(playercode):
    """
    :param playercode: identifies player for which to retrieve today's stats

    retrieves today's stats from MLB boxscore for a specific player
    """

    with open(PLYR_MSTR_I, 'r') as playerMaster:
        players = json.load(playerMaster)

    with open(TEAM_MSTR_I, 'r') as teamMaster:
        teams = json.load(teamMaster)

    teamcode = players[playercode]['club_code']
    result1 = {}
    result2 = {}

    # if a game is scheduled (link on team master), get stats from game
    if "today_1" in teams[teamcode].keys():
        boxurl = BOXSCORE.replace('/_directory_/', teams[teamcode]['today_1'])
        result1 = apifuncs.get_today_stats(boxurl,
                                           teams[teamcode]['today_home_away'],
                                           playercode)

    # if a double header is scheduled, get stats from that game too
    if "today_2" in teams[teamcode].keys():
        boxurl = BOXSCORE.replace('/_directory_/', teams[teamcode]['today_2'])
        result2 = apifuncs.get_today_stats(teams[teamcode]['today_2'],
                                           teams[teamcode]['today_home_away'],
                                           playercode)

    # add stats together from both games though there is usually only one
    result = apifuncs.add_todays_results(result1,
                                         result2,
                                         playercode,
                                         players[playercode]['full_name'],
                                         players[playercode]['position'],
                                         teams[teamcode]['club_short'])

    # convert dictionary result to a string and return
    result_str = json.dumps(result)
    return result_str
