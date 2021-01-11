"""
Defines the classes and methods associated with connecting to showdown and
battling. Reads information from login.json to connect to the Pokemon Showdown
server, then communcates using websocket messages.
"""

import websockets
import requests
import asyncio
import json
import logging

class PSSock():
    sock = None

    def __init__(self, login='login.json', address='sim.smogon.com', port=8000): 
        self.log = logging.getLogger(__name__)
        self.uri = f'ws://{address}:{port}/showdown/websocket'
        self.login_uri = 'https://play.pokemonshowdown.com/action.php'
        with open(login) as json_file:
            login_info = json.load(json_file)
            self.username = login_info['username']
            self.password = login_info['password']

    def __del__(self):
        if self.sock:
            self.sock.close()

    def start(self):
        asyncio.run(self.__login_and_listen())

    async def __login_and_listen(self):
        self.log.warn(f'Connecting to {self.uri}')
        async with websockets.connect(self.uri) as ws:
            challstr = await self.__wait_for_msg(ws, 'challstr')
            response = requests.post(
                self.login_uri,
                data={
                    'act': 'login',
                    'name': self.username,
                    'pass': self.password,
                    'challstr': f'{challstr[1]}|{challstr[2]}'
                }
            )
            if response.status_code == 200:
                response_json = json.loads(response.text[1:])
                if not response_json['actionsuccess']:
                    raise RuntimeError(f'Error logging in.\n{response.content}')
                assertion = response_json['assertion']
                await ws.send(f'|/trn {self.username},0,{assertion}')
                self.log.warn("Login successful.")
                self.log.warn(json.dumps(response_json, indent=3))
            else:
                raise RuntimeError(f'Error logging in.\n{response.content}')

    async def __handle_response(self, response):
        pass

    async def __wait_for_msg(self, ws, msgtype):
        while True:
            message = await ws.recv()
            message = message.split("|")[1:]
            if message[0] == msgtype:
                return message
        
