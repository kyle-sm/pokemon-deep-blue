"""
The main module. This is the entrypoint to all operations related
to running and training the bot.
"""
import sys
import getopt
import logging


LOG_LEVEL_DICT = {
    "CRITICAL" : logging.CRITICAL,
    "ERROR" : logging.ERROR,
    "WARNING" : logging.WARNING,
    "INFO" : logging.INFO,
    "DEBUG" : logging.DEBUG
}


def main():
    """The main method. Processes flags to determine how to run the program."""
    mainlogger = logging.getLogger(__name__)

    # Read through flags and set variables accordingly
    try:
        opts, args = getopt.getopt(sys.argv[1:], "l:", ["loglevel="])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-l", "--loglevel"):
            logging.basicConfig(level=LOG_LEVEL_DICT[arg])
    return


if __name__ == "__main__":
    main()
