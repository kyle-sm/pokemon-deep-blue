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

class PSClient():

    socket = None
    stop = False

    def __init__(self, login='login.json', address='sim.smogon.com', port=8000): 
        self.log = logging.getLogger(__name__)
        self.uri = f'ws://{address}:{port}/showdown/websocket'
        self.login_uri = 'https://play.pokemonshowdown.com/action.php'
        self.battlerooms = dict()
        # if the format doesn't require a team, initialize it to null
        self.teams = {'gen8randombattle' : 'null'}

    def __del__(self):
        if self.socket:
            asyncio.run(self.socket.close())


    """
    Opens a websocket connection and attempts to log in using the fields the
    class was initialized with. Must be called before doing anything else.
    """
    async def login(self, login_file='login.json'):
        username = ''
        password = ''
        with open(login_file) as json_file:
            login_info = json.load(json_file)
            username = login_info['username']
            password = login_info['password']
        self.log.debug(f'Connecting to {self.uri}...')
        self.socket = await websockets.connect(self.uri)
        challstr = await self.__wait_for_msg(type='challstr')
        response = requests.post(
            self.login_uri,
            data={
                'act': 'login',
                'name': username,
                'pass': password,
                'challstr': f"{challstr['content'][0]}|{challstr['content'][1]}"
            }
        )
        if response.status_code == 200:
            response_json = json.loads(response.text[1:])
            self.log.info('login request response:\n' + json.dumps(response_json, indent=3))
            if not response_json['actionsuccess']:
                raise RuntimeError(f'Error logging in.\n{response.content}')
            assertion = response_json['assertion']
            await self.socket.send(f'|/trn {username},0,{assertion}')
            self.log.warn("Login successful.")
        else:
            raise RuntimeError(f'Error logging in.\n{response.content}')

    """
    Loads a team through the websocket. Type can be either json, packed, or
    webexport, with webexport being the format that the Pokemon Showdown webclient
    exports team as. Returns False if trying to add a team for a format that
    doesn't need one.
    """
    async def load_team(self, format, filename, type):
        if self.teams.get(format, '') == 'null':
            return False
        with open(filename, 'r') as team_file:
            if type == 'packed':
                self.teams[format] = team_file.read()
            if type == 'webexport':
                pass

    
    """
    Starts the main loop which receives and acts on messages sent through the
    websocket. Will continue until stop() is called. Based on what it receives,
    it will create additional tasks to deal with them, or use queues to send
    them to preexisting tasks.
    """
    async def play(self):
        self.stop = False
        while not self.stop:
            msg = await self.__wait_for_msg()
            if msg['room'] in self.battlerooms:
                await self.battlerooms[msg['room']].put(msg)
            elif msg['type'] == 'updatechallenges':
                asyncio.create_task(self.__accept_challenge(msg))
            elif msg['type'] == 'init':
                msg_queue = asyncio.Queue()
                self.battlerooms[msg['room']] = msg_queue
                asyncio.create_task(self.__battle_routine(msg_queue, msg['room']))
            elif msg['type'] == 'error':
                self.log.warn(f'Websocket sent an error: {msg[2]}')

    
    """Tells a currently playing client to stop."""
    async def stop(self):
        pass

    """
    Waits for a message from the websocket, optionally of the specified type or
    room. Returns a dictionary that contains the room, message type, and message
    content. 
    """
    async def __wait_for_msg(self, **kwargs):
        if not self.socket:
            self.log.error('Attempted to listen without an open socket')
            raise RuntimeError('Attempted to listen without an open socket')
        while True:
            message = await self.socket.recv()
            message = message.split('|')
            if kwargs.get('type', '') in message[1] and kwargs.get('room', '') in message[0]:
                if not message[0] == '':
                    message[0] = message[0].rstrip()[1:]
                return { 
                        'room' : message[0],
                        'type' : message[1],
                        'content' : message[2:]
                        }

    """
    Sends a message if the socket is open. Can specify room if
    necessary.
    """
    async def __send_msg(self, message, **kwargs):
        if not self.socket:
            self.log.error('Attempted to send without an open socket')
            raise RuntimeError('Attempted to send without an open socket')
        await self.socket.send(
          f"{kwargs.get('room','')}|{message}")


    async def __accept_challenge(self, msg):
        json_data = json.loads(msg['content'][0])
        for username, format in json_data['challengesFrom'].items():
            if format in self.teams:
                await self.__send_msg(f'/utm {self.teams[format]}')
                await self.__send_msg(f'/accept {username}')
            else:
                await self.__send_msg(f'/w {username}, I don\'t have a team for that format.')
                await self.__send_msg(f'/reject {username}')
                
    # This is a temporary battle routine that randomly chooses moves
    async def __battle_routine(self, msgs, roomid):
        self.log.warn(f'Joining {roomid}...')
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
                        if not pkmn['active'] and 'fnt' not in pkmn['condition']:
                            choices.append(index + 1)
                    choice = choices[random.randint(0, len(choices)-1)]
                    await self.__send_msg(f'/switch {choice}', room=roomid)
                else:
                    for move in rjson['active'][0]['moves']:
                        if not move['disabled']:
                            choices.append(move['id'])
                    choice = choices[random.randint(0, len(choices)-1)]
                    await self.__send_msg(f'/move {choice}', room=roomid)
            elif 'win' in msg['content'] or 'draw' in msg['content']:
                await self.__send_msg(f'/leave {roomid}', room=roomid)
                del self.battlerooms[roomid]
                return
