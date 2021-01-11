"""
The main module. This is the entrypoint to all operations related
to running and training the bot.
"""
import sys
import getopt
import logging
import websockets
import asyncio

import trainer
import battler

LOG_LEVEL_DICT = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG
}


def main():
    """The main method. Processes flags to determine how to run the program."""
    mainlogger = logging.getLogger(__name__)
    battle_format = "gen8ou"

    # Read through flags and set variables accordingly
    try:
        opts, args = getopt.getopt(sys.argv[1:], "l:f:htb", ["loglevel=", "battleformat=", "help"])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-l", "--loglevel"):
            try:
                logging.basicConfig(level=LOG_LEVEL_DICT[arg])
            except KeyError as err:
                print(f'Invalid log level passed to {opt}.',
                       '\nValid arguments are CRITICAL, ERROR,',
                       'WARNING, INFO, and DEBUG.')
                sys.exit(2)
        elif opt in ('-f', '--battleformat'):
            battle_format = arg;
        elif opt in ('-h', '--help'):
            print('-f, --battleformat=:\n\tSet battle format (default gen8ou)',
                  '\n-l, --loglevel=:\n\tSet log level (default WARNING)',
                  '\n-h, --help:\n\tDisplay help message')
            sys.exit(2)
        elif opt == '-t':
            trainer.get_training_data(battle_format)
        elif opt == '-b':
            sock = battler.PSSock()

    return

async def test():
    uri = 'ws://sim.smogon.com:8000/showdown/websocket'
    async with websockets.connect(uri) as ws:
        await ws.send('|/join lobby')
        await ws.send('|/query roomlist')
        recv = await ws.recv()
        print(recv)
        recv = await ws.recv()
        print(recv)
        recv = await ws.recv()
        print(recv)
        recv = await ws.recv()
        print(recv)
        recv = await ws.recv()
        print(recv)
        recv = await ws.recv()
        print(recv)
        recv = await ws.recv()
        print(recv)
        recv = await ws.recv()
        print(recv)

asyncio.get_event_loop().run_until_complete(test()) 

if __name__ == "__main__":
    main()

