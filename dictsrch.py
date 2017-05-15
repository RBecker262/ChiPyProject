"""
MLB Gameday Retrieval - Search Dictionary
Author: Robert Becker
Date: May 13, 2017
Purpose: Recursive functions used to find desired data in json dictionary
"""


import logging


def search_dictionary(indict, resultdict):
    """
    Input parameters:
    indict     = dictionary to be parsed
    resultdict = result dictionary, starts blank and updated for each new entry

    Function loops through dictionary keys and examines values
    If function finds a nested dictionary, call itself to parse next level
    If function finds a list, call listlevel to parse the list
    As soon as game data is found return to previous recursion level
    """

    logger = logging.getLogger(__name__)

    # get dictionary key list from and create entry in result dictionary
    keylist = list(indict.keys())

    if 'game_data_directory' in keylist:
        # print('Keys where GDD found...' + str(keylist))
        gcstart = len(indict['game_data_directory']) - 15
        gamecode = indict['game_data_directory'][gcstart:]
        entry = {gamecode:
                 {"directory": indict['game_data_directory'],
                  "away_code": indict['away_code'],
                  "home_code": indict['home_code']}}
        resultdict.update(entry)
        logger.debug(gamecode + " entry added to result dictionary")

        return resultdict

    # loop thru each dictionary entry at the current level
    for dictkey in keylist:

        # test if current value is a nested dictionary
        if isinstance(indict[dictkey], dict):

            # recursive call to search nested dictionary
            resultdict = search_dictionary(indict[dictkey], resultdict)

        # test if current value is a list
        elif isinstance(indict[dictkey], list):

            # call function to search list
            resultdict = search_list(indict[dictkey], resultdict)

    # return whatever is in result dicionary at end of this dictionary level
    return resultdict


def search_list(inlist, resultdict):
    """
    Input parameters:
    inlist     = list to be parsed
    resultdict = result dictionary, starts blank and updated for each new entry

    Function loops through a list and examines list entries
    If function finds a nested dictionary, it calls dictlevel
    If function finds a list, it calls itself to parse the list
    """

    # loop thru each list entry at the current level
    for listentry in inlist:

        # test if current list entry is a nested dictionary
        if isinstance(listentry, dict):

            # recursive call to search nested dictionary
            resultdict = search_dictionary(listentry, resultdict)

        # test if current entry is a list
        elif isinstance(listentry, list):

            # recursive call to search nested list
            resultdict = search_list(listentry, resultdict)

    # return whatever is in result dicionary at end of this list
    return resultdict
