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
import random

class PSSock():

    def __init__(self, login='login.json', address='sim.smogon.com', port=8000): 
        self.log = logging.getLogger(__name__)
        self.uri = f'ws://{address}:{port}/showdown/websocket'
        self.login_uri = 'https://play.pokemonshowdown.com/action.php'
        with open(login) as json_file:
            login_info = json.load(json_file)
            self.username = login_info['username']
            self.password = login_info['password']

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
                    'challstr': f'{challstr[2]}|{challstr[3]}'
                }
            )
            if response.status_code == 200:
                response_json = json.loads(response.text[1:])
                self.log.info('login request response:\n' + json.dumps(response_json, indent=3))
                if not response_json['actionsuccess']:
                    raise RuntimeError(f'Error logging in.\n{response.content}')
                assertion = response_json['assertion']
                await ws.send(f'|/trn {self.username},0,{assertion}')
                self.log.warn("Login successful.")
            else:
                raise RuntimeError(f'Error logging in.\n{response.content}')
            while True:
                challenge = await self.__wait_for_msg(ws, 'updatechallenges')
                json_data = json.loads(challenge[2])
                for username, format in json_data['challengesFrom'].items():
                    await ws.send(f'|/utm null')
                    await ws.send(f'|/accept {username}')
                    initmsg = await self.__wait_for_msg(ws, 'init')
                    await self.__battle_routine(ws, initmsg[0].rstrip())

    async def __wait_for_msg(self, ws, msgtype='', room=''):
        while True:
            message = await ws.recv()
            message = message.split('|')
            print(message)
            if (msgtype == '' or message[1] == msgtype): 
                if (room == '' or message[0] == room):
                    return message

    # the current implementation is a placeholder that does random action to
    # test the connection. Once a proper training method is implemented, the AI
    # will make proper, intelligent decisions
    async def __battle_routine(self, ws, roomid):
        print(roomid)
        while True:
            await ws.send(f'{roomid}|/choose move {random.randint(1,4)}')
            await asyncio.sleep(20)
            await ws.send(f'{roomid}|/switch {random.randint(1,6)}')

