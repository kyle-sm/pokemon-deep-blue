"""
Defines the PSClient class, which connects to a showdown websocket with the
provided information and handles websocket messages asyncronously.
"""

import websockets
import requests
import asyncio
import json
import logging

class PSClient()

    socket = None
    stop = False

    def __init__(self, login='login.json', address='sim.smogon.com', port=8000): 
        self.log = logging.getLogger(__name__)
        self.uri = f'ws://{address}:{port}/showdown/websocket'
        self.login_uri = 'https://play.pokemonshowdown.com/action.php'
        self.battlerooms = dict()
        # if the format doesn't require a team, initialize it to null
        self.teams = {'gen8randombattle' : 'null'}
        with open(login) as json_file:
            login_info = json.load(json_file)
            self.username = login_info['username']
            self.password = login_info['password']

    def __del__(self):
        if socket:
            socket.close()


    """
    Opens a websocket connection and attempts to log in using the fields the
    class was initialized with. Must be called before doing anything else.
    """
    async def login(self):
        self.log.debug(f'Connecting to {self.uri}...')
        async with websockets.connect(self.uri) as self.socket:
        challstr = await self.__wait_for_msg(type='challstr')
        response = requests.post(
            self.login_uri,
            data={
                'act': 'login',
                'name': self.username,
                'pass': self.password,
                'challstr': f"{challstr['content'][0]]}|{challstr['content'][1]}"
            }
        )
        if response.status_code == 200:
            response_json = json.loads(response.text[1:])
            self.log.info('login request response:\n' + json.dumps(response_json, indent=3))
            if not response_json['actionsuccess']:
                raise RuntimeError(f'Error logging in.\n{response.content}')
            assertion = response_json['assertion']
            await self.socket.send(f'|/trn {self.username},0,{assertion}')
            self.log.warn("Login successful.")
        else:
            raise RuntimeError(f'Error logging in.\n{response.content}')

    """
    Loads a team through the websocket. Type can be either json, packed, or
    webexport, with webexport being the format that the Pokemon Showdown webclient
    exports team as. 
    """
    async def load_team(self, filename, type):
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
            msg = await self.__wait_for_message(self)
            if(msg['room'] in self.battlerooms):
                self.battlerooms[msg[0]].put(msg)
            elif(msg['type'] == 'updatechallenges'):
                asyncio.create_task(self.__accept_challenge(msg))
            elif(msg['type'] == 'error'):
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
                if not message[0] == ''
                    message[0] = message[0].rstrip()[1:]
                return { 
                        'room' : message[0],
                        'type' : message[1],
                        'content' : message[2:]
                        }

    """
    Sends a message if the socket is open. Can specify room and type if
    necessary.
    """
    async def __send_msg(self, message, **kwargs):
        if not self.socket:
            self.log.error('Attempted to send without an open socket')
            raise RuntimeError('Attempted to send without an open socket')
        await self.socket.send(
          f"{kwargs.get('room','')}|{kwargs.get('room','')}|{message}")


    async def __accept_battle(self, msg):
        json_data = json.loads(msg[2])
        for username, format in json_data['challengesFrom'].items():
            if format in self.teams:
                await self.__send_msg(f'/utm {self.teams[format]}')
                await self.__send_msg(f'/accept {username}')
                initmsg = await self.wait_for_msg(type='init')
                room = initmsg[0].rstrip()[1:]
                msg_queue = asyncio.Queue()
                battlerooms[room] = msg_queue
                asyncio.create_task(self.__battle_routine(msq_queue))
            else:
                await self.__send_msg(f'/w {username}, I don\'t have a team for that format.')
                await self.__send_msg(f'/reject {username}')
                
