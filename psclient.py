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

    def __init__(self, login='login.json', address='sim.smogon.com', port=8000): 
        self.log = logging.getLogger(__name__)
        self.uri = f'ws://{address}:{port}/showdown/websocket'
        self.login_uri = 'https://play.pokemonshowdown.com/action.php'
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
                'challstr': f'{challstr[2]}|{challstr[3]}'
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
    Loads a team through the websocket. Type can be either json or plaintext, with
    plaintext being the format that the Pokemon Showdown webclient exports team
    as. 
    """
    async def load_team(self, filename, type):
        pass
    
    """
    Starts the main loop which receives and acts on messages sent through the
    websocket. Will continue until stop() is called.
    """
    async def play(self):
        pass
    
    """
    Tells a currently playing client to stop.
    """
    async def stop(self):
        pass

    """Waits for a message from the websocket, optionally of the specified type or room"""
    async def __wait_for_msg(self, **kwargs):
        if not socket:
            self.log.error('Attempted to listen without an open socket')
            raise RuntimeError('Attempted to listen without an open socket')
        while True:
            message = await self.socket.recv()
            message = message.split('|')
            if kwargs.get('type', '') in message[1] and kwargs.get('room', '') in message[0]:
                    return message
