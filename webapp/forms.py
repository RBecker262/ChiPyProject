from flask_wtf import Form
from wtforms import StringField, BooleanField


class HomeForm(Form):
    displastname = BooleanField('Display Last Name on Web Page')


class AboutForm(Form):
    displastname = BooleanField('Display Last Name on Web Page')


class ByLastNameForm(Form):
    displastname = BooleanField('Display Last Name on Web Page')
    lastname = StringField('Last Name')


class ByTeamForm(Form):
    displastname = BooleanField('Display Last Name on Web Page')
    teamcode = StringField('Team Code')


class PlayerStatsForm(Form):
    displastname = BooleanField('Display Last Name on Web Page')
    lastname = StringField('Last Name')
    teamcode = StringField('Team Code')
    playercode = StringField('Player Code')


class VanAllanEffectForm(Form):
    displastname = BooleanField('Display Last Name on Web Page')


class WatchListForm(Form):
    displastname = BooleanField('Display Last Name on Web Page')
