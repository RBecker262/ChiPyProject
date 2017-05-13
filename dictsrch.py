"""
Parse Dictionary Function Library
Author: Robert Becker
Date: April 17, 2017
Purpose: Recursive functions used to find player data in json dictionary
"""


import logging


def search_dictionary(indict):
    """
    Input parameters:
    indict  = dictionary to be parsed

    Function loops through dictionary keys and examines values
    If function finds a nested dictionary, call itself to parse next level
    If function finds a list, call listlevel to parse the list
    If function finds a normal value, it writes output file if desired
    As soon as player data is found return to previous recursion level
    """

    logger = logging.getLogger(__name__)

    # get dictionary key list from current level and return if it's our player
    keylist = list(indict.keys())

    if 'game_data_directory' in keylist:
        print('away: ' + indict["away_code"])
        print('home: ' + indict["home_code"])
        print('directory ' + indict[u'game_day_directory'])
        # entry1 = {"game_code": indict['game_day_directory'][15:],
        #            "data": {"away_code": indict['away_code'],
        #                    "home_code": indict['home_code'],
        #                    "game_dir": indict['game_day_directory']}}

        return indict

    # loop thru each dictionary key at the current level
    for dictkey in keylist:

        # test if current value is a nested dictionary
        if isinstance(indict[dictkey], dict):

            # recursive call to parse nested dictionary, increase level #
            logger.debug('Recursive call to search for key: ' + dictkey)

            myplayerdata = search_dictionary(indict[dictkey])

            logger.debug('Returned from recursive call for key: ' + dictkey)

            # if player data found, return data to previous recursion level
            if myplayerdata:
                return myplayerdata

        # test if current value is a list
        elif isinstance(indict[dictkey], list):

            # call function to search list, level stays same
            logger.debug('Call search_list for dictionary key: ' + dictkey)

            myplayerdata = search_list(indict[dictkey])

            logger.debug('Returned from parsing list for key: ' + dictkey)

            # If player data found, return data to previous recursion level
            if myplayerdata:
                return myplayerdata

    # return empty dictionary if nothing found within this level
    return {}


def search_list(inlist):
    """
    Input parameters:
    inlist  = list to be parsed

    Function loops through a list and examines list entries
    If function finds a nested dictionary, it calls dictlevel
    If function finds a list, it calls itself to parse the list
    As soon as player data is found return to previous recursion level
    """

    logger = logging.getLogger(__name__)

    # loop thru each list entry at the current level
    for listentry in inlist:

        # test if current list entry is a nested dictionary
        if isinstance(listentry, dict):

            # recursive call to parse nested dictionary, increase level #
            logger.debug('Recursive call search_dictionary from search_list')

            myplayerdata = search_dictionary(listentry)

            # if player data found, return data to previous recursion level
            if myplayerdata:
                return myplayerdata

        # test if current entry is a list
        elif isinstance(listentry, list):

            # recursive call to search nested list, level stays the same
            logger.debug('Recursive call to listlevel function')

            myplayerdata = search_list(listentry)

            logger.debug('Returned from recursive call to search_list')

            # if player data found, return data to previous recursion level
            if myplayerdata:
                return myplayerdata

    # return empty dictionary if nothing found within this level
    return {}
