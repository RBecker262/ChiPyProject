
import unittest

from webapp import apifuncs

# README
# Execute these with
#
# $ python -m unittest


BRYANT_RESULT1 = {
    'batting': {
        'a': '0',
        'ab': '4',
        'ao': '1',
        'avg': '.000',
        'bb': '0',
        'bo': '200',
        'cs': '0',
        'd': '0',
        'e': '0',
        'fldg': '.000',
        'h': '0',
        'hbp': '0',
        'hr': '0',
        'id': '592178',
        'lob': '5',
        'name': 'Bryant',
        'name_display_first_last': 'Kris Bryant',
        'obp': '.000',
        'ops': '.000',
        'po': '0',
        'pos': '3B',
        'r': '0',
        'rbi': '0',
        's_bb': '0',
        's_h': '0',
        's_hr': '0',
        's_r': '0',
        's_rbi': '0',
        's_so': '3',
        'sac': '0',
        'sb': '0',
        'sf': '0',
        'slg': '.000',
        'so': '3',
        't': '0'
    }
}


BRYANT_TODAYS_BATTING = {
    'Bryant': {
        'team': 'chn',
        'code': 'Bryant',
        'hr': 0,
        'rbi': 0,
        'walks': 0,
        'name': 'Kris Bryant',
        'runs': 0,
        'avg': 4,
        'pos': '3B',
        'hits': 0
    }
}


class AddTodaysBattingTestCase(unittest.TestCase):

    def test_vanilla(self):
        result = apifuncs.add_todays_batting(
            BRYANT_RESULT1,
            {},
            'Bryant',
            'Kris Bryant',
            '3B',
            'chn',
        )
        self.assertEqual(BRYANT_TODAYS_BATTING, result)
