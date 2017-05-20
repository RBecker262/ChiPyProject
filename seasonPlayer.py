"""
seasonPlayer.py
Author: Robert Becker
Date: May 19, 2017
Purpose: used to drive

Read config file to get location of the master scoreboard
Load dictionary into memory
Call search_dictionary to get directory information for all MLB games today
"""


import sys
import argparse
import logging
import logging.config
import dailySchedule
import playerMaster


# setup global variables
SCRIPT = 'seasonPlayer.py'
LOGGING_INI = 'seasonPlayer_logging.ini'


def init_logger():
    """
    initialize global variable logger and set script name
    """

    global logger
    logger = logging.getLogger(SCRIPT)


def get_command_arguments():
    """
    --date  optional, will extract schedules for this date if provided
    """

    parser = argparse.ArgumentParser('seasonPlayer command line arguments')
    parser.add_argument(
        '-d',
        '--date',
        help='Date of daily schedule for input - mm-dd-yyyy format',
        dest='game_date',
        type=str)

    argue = parser.parse_args()
    logger.info('Command arguments: ' + str(argue.game_date))

    return argue


def main(gamedate=None):

    rc = dailySchedule.invoke_dailySchedule_as_sub(gamedate)
    logger = logging.getLogger(SCRIPT)
    logger.info('dailySchedule sub-function completed with code: ' + str(rc))

    if rc == 0:
        rc = playerMaster.invoke_playerMaster_as_sub(gamedate)
        logger = logging.getLogger(SCRIPT)
        logger.info('playerMaster subfunction completed with code: ' + str(rc))

    return rc


if __name__ == '__main__':
    logging.config.fileConfig(LOGGING_INI)
    init_logger()
    logger.info('Executing script as main function')

    args = get_command_arguments()

    cc = main(args.game_date)

    logger.info('Completion code: ' + str(cc))
    sys.exit(cc)
