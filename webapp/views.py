from flask import render_template, redirect, flash, request, url_for
import requests
import json
from webapp import webapp
from .forms import HomeForm, AboutForm, ByLastNameForm, ByTeamForm
from .forms import PlayerStatsForm, WatchListForm, VanAllanEffectForm

API_SERVER = 'http://127.0.0.1:5001'


def get_season_stats(api_url):

    api_resp = requests.get(api_url)
    api_str = api_resp.content.decode()
    loaded = json.loads(api_str)
    batters = []
    pitchers = []
    for key in sorted(loaded['batters'].keys()):
        batters.append(loaded['batters'][key])
    for key in sorted(loaded['pitchers'].keys()):
        pitchers.append(loaded['pitchers'][key])

    return (batters, pitchers)


def get_todays_stats(api_url):

    api_resp = requests.get(api_url)
    api_str = api_resp.content.decode()
    loaded = json.loads(api_str)
    batters = []
    pitchers = []
    for key in sorted(loaded['batters'].keys()):
        batters.append(loaded['batters'][key])
    for key in sorted(loaded['pitchers'].keys()):
        pitchers.append(loaded['pitchers'][key])

    return (batters, pitchers)


@webapp.route('/')
@webapp.route('/index')
@webapp.route('/TheSandlot')
def thesandlot():
    form = HomeForm()
    flash("Welcome to Rob's Sandlot!")

    return render_template("base.html", title='Home', form=form, errors=False)


@webapp.route('/ByTeam', methods=['GET', 'POST'])
def byteam():
    form = ByTeamForm()
    if form.teamcode.data is not None:
        return redirect(url_for('playerstats', teamcode=form.teamcode.data))
    url = API_SERVER + '/allteams'
    api_resp = requests.get(url)
    api_str = api_resp.content.decode()
    loaded = json.loads(api_str)
    teams = []
    for key in sorted(loaded.keys()):
        teams.append(loaded[key])
    flash('Click on row to view team roster / stats')

    return render_template("byteam.html", form=form, teams=teams, errors=False)


@webapp.route('/ByLastName', methods=['GET', 'POST'])
def bylastname():
    form = ByLastNameForm()
    lastname = form.lastname.data
    errors = False
    if request.method == 'POST':
        if len(lastname.strip()) > 0:
            return redirect(url_for('playerstats',
                                    lastname=lastname,
                                    displastname=True))
        else:
            errors = True
    flash('Enter at least 1 letter of player last name:')

    return render_template("base.html",
                           form=form,
                           displastname=True,
                           errors=errors)


@webapp.route('/PlayerStats', methods=['GET', 'POST'])
def playerstats(teamcode=None, lastname=None, displastname=False):
    form = PlayerStatsForm()
    errors = False
    teamcode = request.args.get('teamcode')
    lastname = request.args.get('lastname')
    playercode = form.playercode.data
    if request.method == "GET" and teamcode:
        # request to display all players for team, call teamplayers api
        url = API_SERVER + '/teamplayers/' + teamcode
        list = get_season_stats(url)
        batters = list[0]
        pitchers = list[1]
        form.displastname.data = displastname
        flash("Season stats displayed, toggle player row for today's stats")

    elif request.method == "GET" and lastname:
        # request to display players matching partial name, call lastname api
        displastname = request.args.get('displastname')
        form.displastname.data = displastname
        form.lastname.data = lastname
        url = API_SERVER + '/lastname/' + lastname
        list = get_season_stats(url)
        batters = list[0]
        pitchers = list[1]
        flash("Season stats displayed, toggle player row for today's stats")

    elif playercode is not None and str(playercode).strip() != '':
        # user clicked on player row, call todays stats api
        displastname = form.displastname.data
        if displastname is not None:
            lastname = form.lastname.data
        # batters = apitemp.get_batters_today(playercode)
        # pitchers = apitemp.get_pitchers_today(playercode)
        batters = []
        pitchers = []
        form.playercode.data = playercode
        flash('Stats from games played today')

    else:
        # partial name field updated, if valid call lastname api
        displastname = form.displastname.data
        lastname = form.lastname.data
        if request.method == 'POST' and len(lastname.strip()) > 0:
            url = API_SERVER + '/lastname/' + lastname
            list = get_season_stats(url)
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
                           errors=errors)


@webapp.route('/WatchList')
def watchlist():
    form = WatchListForm()
    flash('View and update the Watch List')

    return render_template("watchlist.html",
                           form=form,
                           displastname=False,
                           errors=False)


@webapp.route('/VanAllanEffect')
def vanallaneffect():
    form = VanAllanEffectForm()
    flash('SAVE THE CARDINALS!')

    return render_template("vanallaneffect.html",
                           form=form,
                           displastname=False,
                           errors=True)


@webapp.route('/About')
def about():
    form = AboutForm()
    flash('Say something nice about Allan, ChiPy, and what I learned')

    return render_template("about.html",
                           form=form,
                           displastname=False,
                           errors=False)
