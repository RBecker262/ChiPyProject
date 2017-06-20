from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField


class HomeForm(FlaskForm):
    displastname = BooleanField('Display Last Name on Web Page')


class AboutForm(FlaskForm):
    displastname = BooleanField('Display Last Name on Web Page')


class ByLastNameForm(FlaskForm):
    displastname = BooleanField('Display Last Name on Web Page')
    lastname = StringField('Last Name')


class ByTeamForm(FlaskForm):
    displastname = BooleanField('Display Last Name on Web Page')
    teamcode = StringField('Team Code')


class PlayerStatsForm(FlaskForm):
    displastname = BooleanField('Display Last Name on Web Page')
    lastname = StringField('Last Name')
    teamcode = StringField('Team Code')
    playercode = StringField('Player Code')


class VanAllanEffectForm(FlaskForm):
    displastname = BooleanField('Display Last Name on Web Page')


class WatchListForm(FlaskForm):
    displastname = BooleanField('Display Last Name on Web Page')
