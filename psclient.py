"""
Defines the PSClient class, which connects to a showdown websocket with the
provided information and handles websocket messages asyncronously.
"""

import websockets
import requests
import asyncio
import json
import logging
import random

log = logging.getLogger(__name__)


class PSClient():
    def __init__(self,
                 login='login.json',
                 address='sim.smogon.com',
                 port=8000):
        self.active = False
        self.socket = None
        # if the format doesn't require a team, initialize it to null
        self.teams = {'gen8randombattle': 'null'}
        self.battlerooms = dict()
        self.uri = f'ws://{address}:{port}/showdown/websocket'
        self.login_uri = 'https://play.pokemonshowdown.com/action.php'

    @property
    def myteams(self):
        return self.teams

    """
    Opens a websocket connection and attempts to log in using the fields the
    class was initialized with. Must be called before doing anything else.
    """

    async def login(self, login_file='login.json'):
        log.debug('Attempting to log in...')
        username = ''
        password = ''
        with open(login_file) as json_file:
            login_info = json.load(json_file)
            username = login_info['username']
            password = login_info['password']
        log.debug(f'Connecting to {self.uri}...')
        self.socket = await websockets.connect(self.uri)
        challstr = await self.__wait_for_msg(type='challstr')
        response = requests.post(
            self.login_uri,
            data={
                'act': 'login',
                'name': username,
                'pass': password,
                'challstr':
                f"{challstr['content'][0]}|{challstr['content'][1]}"
            })
        if response.status_code == 200:
            response_json = json.loads(response.text[1:])
            log.info('login request response:\n' +
                     json.dumps(response_json, indent=3))
            if not response_json['actionsuccess']:
                raise RuntimeError(f'Error logging in.\n{response.content}')
            assertion = response_json['assertion']
            await self.socket.send(f'|/trn {username},0,{assertion}')
            log.debug("Login successful.")
        else:
            raise RuntimeError(f'Error logging in.\n{response.content}')

    """
    Loads team from a file in the format that showdown exports in. If packed is
    set to True, it assumes the team is already in the packed format. Returns
    False if the format specified does not require a team.
    """

    def load_team(self, format, filename, packed=False):
        # TODO: this is dumb
        if self.teams.get(format, '') == 'null':
            return False
        with open(filename, 'r') as team_file:
            if packed:
                self.teams[format] = team_file.read()
                return True
            team = ''
            mon = {
                'nick': '',
                'species': '',
                'item': '',
                'ability': '',
                'moves': list(),
                'nature': '',
                'evHP': '',
                'evAtk': '',
                'evDef': '',
                'evSpA': '',
                'evSpD': '',
                'evSpe': '',
                'gender': '',
                'ivHP': '',
                'ivAtk': '',
                'ivDef': '',
                'ivSpA': '',
                'ivSpD': '',
                'ivSpe': '',
                'shiny': '',
                'level': ''
            }
            for line in team_file:
                split = line.strip().split(' ')
                if 'Ability:' in split:
                    mon['ability'] = self.__pokeparse_helper(line[9:])
                elif 'Nature' in split:
                    mon['nature'] = split[0].lower()
                elif 'EVs:' in split:
                    for index, word in enumerate(split):
                        if word.isdigit():
                            mon['ev' + split[index + 1]] = word
                elif 'IVs:' in split:
                    for index, word in enumerate(split):
                        if word.isdigit():
                            mon['iv' + split[index + 1]] = word
                elif 'Shiny:' in split:
                    mon['shiny'] = 'S'
                elif 'Level:' in split:
                    mon['level'] = split[1]
                elif '-' == split[0]:
                    mon['moves'].append(self.__pokeparse_helper(line[2:]))
                elif '@' in split:
                    if not mon['nick'] == '':
                        team += ''.join([
                            f"{mon['nick']}|{mon['species']}|{mon['item']}|",
                            f"{mon['ability']}|{','.join(mon['moves'])}|",
                            f"{mon['nature']}|{mon['evHP']},{mon['evAtk']},",
                            f"{mon['evDef']},{mon['evSpA']},{mon['evSpD']},",
                            f"{mon['evSpe']}|{mon['gender']}|",
                            f"{mon['ivHP']},{mon['ivAtk']},{mon['ivDef']},",
                            f"{mon['ivSpA']},{mon['ivSpD']},{mon['ivSpe']}|",
                            f"{mon['shiny']}|{mon['level']}|]"
                        ]).replace('\n', '')
                        mon = {
                            'nick': '',
                            'species': '',
                            'item': '',
                            'ability': '',
                            'moves': list(),
                            'nature': '',
                            'evHP': '',
                            'evAtk': '',
                            'evDef': '',
                            'evSpA': '',
                            'evSpD': '',
                            'evSpe': '',
                            'gender': '',
                            'ivHP': '',
                            'ivAtk': '',
                            'ivDef': '',
                            'ivSpA': '',
                            'ivSpD': '',
                            'ivSpe': '',
                            'shiny': '',
                            'level': ''
                        }
                    item_index = split.index('@')
                    item = ''.join(split[item_index + 1:])
                    mon['item'] = self.__pokeparse_helper(item)
                    for word in split[:item_index]:
                        if word == '(M)':
                            mon['gender'] = 'M'
                        elif word == '(F)':
                            mon['gender'] = 'F'
                        elif word[0] == '(':
                            mon['species'] = word[1:-1]
                        else:
                            mon['nick'] = word
            team += ''.join([
                f"{mon['nick']}|{mon['species']}|{mon['item']}|",
                f"{mon['ability']}|{','.join(mon['moves'])}|",
                f"{mon['nature']}|{mon['evHP']},{mon['evAtk']},",
                f"{mon['evDef']},{mon['evSpA']},{mon['evSpD']},",
                f"{mon['evSpe']}|{mon['gender']}|",
                f"{mon['ivHP']},{mon['ivAtk']},{mon['ivDef']},",
                f"{mon['ivSpA']},{mon['ivSpD']},{mon['ivSpe']}|",
                f"{mon['shiny']}|{mon['level']}|"
            ]).replace('\n', '')
            self.teams[format] = team.strip()
            return True

    """
    Starts the main loop which receives and acts on messages sent through the
    websocket. Will continue until stop() is called. Based on what it receives,
    it will create additional tasks to deal with them, or use queues to send
    them to preexisting tasks.
    """

    async def play(self):
        self.active = True
        log.debug('Listening on socket connected to {self.uri}')
        while self.active:
            msg = await self.__wait_for_msg()
            if msg['room'] in self.battlerooms:
                await self.battlerooms[msg['room']].put(msg)
            elif msg['type'] == 'updatechallenges':
                asyncio.create_task(self.__accept_challenge(msg))
            elif msg['type'] == 'init':
                msg_queue = asyncio.Queue()
                self.battlerooms[msg['room']] = msg_queue
                asyncio.create_task(
                    self.__battle_routine(msg_queue, msg['room']))
            elif msg['type'] == 'error':
                log.warning(f'Websocket sent an error: {msg[2]}')

    """Tells a currently playing client to stop."""

    async def close(self):
        log.debug('Closing active rooms...')
        for roomid in self.battlerooms:
            await self.__send_msg("/forfeit", room=roomid)
        self.battlerooms.clear()
        log.debug('Signalling main routine to close...')
        self.active = False
        log.debug('Telling socket to close...')
        await self.socket.close()

    """
    Waits for a message from the websocket, optionally of the specified type or
    room. Returns a dictionary that contains the room, message type, and
    message content.
    """

    async def __wait_for_msg(self, **kwargs):
        if not self.socket:
            log.error('Attempted to listen without an open socket')
            raise RuntimeError('Attempted to listen without an open socket')
        while True:
            message = await self.socket.recv()
            log.debug('recv: {message}')
            message = message.split('|')
            if kwargs.get('type', '') in message[1] and kwargs.get(
                    'room', '') in message[0]:
                if not message[0] == '':
                    message[0] = message[0].rstrip()[1:]
                return {
                    'room': message[0],
                    'type': message[1],
                    'content': message[2:]
                }

    """
    Sends a message if the socket is open. Can specify room if
    necessary.
    """

    async def __send_msg(self, message, **kwargs):
        if not self.socket:
            log.error('Attempted to send without an open socket')
            raise RuntimeError('Attempted to send without an open socket')
        msg = f"{kwargs.get('room','')}|{message}"
        await self.socket.send(msg)
        log.debug(f'send: {msg}')

    async def __accept_challenge(self, msg):
        json_data = json.loads(msg['content'][0])
        for username, format in json_data['challengesFrom'].items():
            if format in self.teams:
                await self.__send_msg(f'/utm {self.teams[format]}')
                await self.__send_msg(f'/accept {username}')
            else:
                await self.__send_msg(
                    f'/w {username}, I don\'t have a team for that format.')
                await self.__send_msg(f'/reject {username}')

    # This is a temporary battle routine that randomly chooses moves
    async def __battle_routine(self, msgs, roomid):
        log.debug(f'Joining {roomid}...')
        await self.__send_msg('/join {roomid}')
        while True:
            msg = await msgs.get()
            if msg['type'] == 'request' and not msg['content'][0] == '':
                rjson = json.loads(msg['content'][0])
                if rjson.get('wait', False):
                    continue
                choices = list()
                if rjson.get('forceSwitch', False):
                    for index, pkmn in enumerate(rjson['side']['pokemon']):
                        if not pkmn['active'] and 'fnt' not in pkmn[
                                'condition']:
                            choices.append(index + 1)
                    choice = choices[random.randint(0, len(choices) - 1)]
                    await self.__send_msg(f'/switch {choice}', room=roomid)
                else:
                    for move in rjson['active'][0]['moves']:
                        if not move['disabled']:
                            choices.append(move['id'])
                    choice = choices[random.randint(0, len(choices) - 1)]
                    await self.__send_msg(f'/move {choice}', room=roomid)
            elif 'win' in msg['content'] or 'draw' in msg['content']:
                await self.__send_msg(f'/leave {roomid}', room=roomid)
                del self.battlerooms[roomid]
                return

    def __pokeparse_helper(self, name):
        return name.replace(' ', '').replace('-', '').lower()
