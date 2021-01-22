"""
The main module. This is the entrypoint to all operations related
to running and training the bot.
"""
import sys
import getopt
import logging
import asyncio

import agent.trainer as trainer
from psclient.psclient import PSClient

LOG_LEVEL_DICT = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG
}


async def main():
    """The main method. Processes flags to determine how to run the program."""
    battle_format = "gen8ou"
    mode = None

    # Read through flags and set variables accordingly
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], "l:f:htbg:",
            ["loglevel=", "battleformat=", "help", "logfile="])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-l", "--loglevel"):
            try:
                logging.basicConfig(level=LOG_LEVEL_DICT[arg])
            except KeyError:
                print(f'Invalid log level passed to {opt}.',
                      '\nValid arguments are CRITICAL, ERROR,',
                      'WARNING, INFO, and DEBUG.')
                sys.exit(2)
        elif opt in ('-f', '--battleformat'):
            battle_format = arg
        elif opt in ('-h', '--help'):
            print('-f, --battleformat=:\n\tSet battle format (default gen8ou)',
                  '\n-l, --loglevel=:\n\tSet log level (default WARNING)',
                  '\n-h, --help:\n\tDisplay help message')
            sys.exit(2)
        elif opt in ('-g', '--logfile'):
            logging.basicConfig(handlers=[logging.FileHandler(arg)])
        elif opt == '-t':
            mode = 1
        elif opt == '-b':
            mode = 2
    if mode == 1:
        trainer.get_training_data(battle_format)
    elif mode == 2:
        client = PSClient()
        await client.login()
        await client.play()
    return


if __name__ == "__main__":
    asyncio.run(main())
