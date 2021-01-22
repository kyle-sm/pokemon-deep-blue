import unittest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, mock_open

from psclient.psclient import PSClient


class TestPSClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.loop = asyncio.get_event_loop()
        cls.packed_team = (
            'Barry|Barraskewda|aguavberry|swiftswim|agility,aquajet,'
            'brickbreak,closecombat|adamant|,252,,,4,252|M|30,,30,30,,30|S||]'
            'Blissey||assaultvest|naturalcure|aromatherapy,avalanche,'
            'blizzard,bodyslam|relaxed|252,4,252,,,|F|,,,,,||99|]'
            'Buzzwole||choiceband|beastboost|bodyslam,brickbreak,'
            'bulkup,closecombat|adamant|252,252,,,4,||,,,,,|||]'
            'Cinderace||aguavberry|libero|acrobatics,agility,'
            'counter,courtchange|adamant|,252,,,4,252||,,,,,|||]'
            'Clefable||aguavberry|unaware|aromatherapy,dazzlinggleam,'
            'blizzard,bodyslam|sassy|252,4,,,252,||,,,,,|||]'
            'Corviknight||aguavberry|mirrorarmor|agility,airslash,'
            'bodypress,bodyslam|naughty|,252,,4,,252||,,,,,|||')
        cls.pokepaste = """Barry (Barraskewda) (M) @ Aguav Berry
Ability: Swift Swim
Shiny: Yes
EVs: 252 Atk / 4 SpD / 252 Spe
Adamant Nature
IVs: 30 HP / 30 Def / 30 SpA / 30 Spe
- Agility
- Aqua Jet
- Brick Break
- Close Combat

Blissey (F) @ Assault Vest
Ability: Natural Cure
Level: 99
EVs: 252 HP / 4 Atk / 252 Def
Relaxed Nature
- Aromatherapy
- Avalanche
- Blizzard
- Body Slam

Buzzwole @ Choice Band
Ability: Beast Boost
EVs: 252 HP / 252 Atk / 4 SpD
Adamant Nature
- Body Slam
- Brick Break
- Bulk Up
- Close Combat

Cinderace @ Aguav Berry
Ability: Libero
EVs: 252 Atk / 4 SpD / 252 Spe
Adamant Nature
- Acrobatics
- Agility
- Counter
- Court Change

Clefable @ Aguav Berry
Ability: Unaware
EVs: 252 HP / 4 Atk / 252 SpD
Sassy Nature
- Aromatherapy
- Dazzling Gleam
- Blizzard
- Body Slam

Corviknight @ Aguav Berry
Ability: Mirror Armor
EVs: 252 Atk / 4 SpA / 252 Spe
Naughty Nature
- Agility
- Air Slash
- Body Press
- Body Slam"""

    @classmethod
    def tearDownClass(cls):
        cls.loop.close()

    def setUp(self):
        self.client = PSClient()

    @patch('psclient.psclient.open')
    @patch('json.load', return_value={'username': 'uname', 'password': 'pass'})
    @patch('websockets.connect',
           new_callable=AsyncMock,
           return_value=AsyncMock(recv=AsyncMock(return_value='|challstr|1|1'))
           )
    @patch('requests.post',
           return_value=Mock(
               status_code=200,
               text=']{"actionsuccess": true,"assertion":"assertion"}'))
    def test_login_success(self, mock_post, mock_connect, mock_json,
                           mock_file):
        self.loop.run_until_complete(self.client.login())
        mock_connect.assert_called_with(
            'ws://sim.smogon.com:8000/showdown/websocket')
        mock_post.assert_called_with(
            'https://play.pokemonshowdown.com/action.php',
            data={
                'act': 'login',
                'name': 'uname',
                'pass': 'pass',
                'challstr': '1|1'
            })
        mock_connect.return_value.send.assert_called_with(
            "|/trn uname,0,assertion")

    @patch('psclient.psclient.open')
    @patch('json.load', return_value={'username': 'uname', 'password': 'pass'})
    @patch('websockets.connect',
           new_callable=AsyncMock,
           return_value=AsyncMock(recv=AsyncMock(return_value='|challstr|1|1'))
           )
    @patch('requests.post', return_value=Mock(status_code=400, content=''))
    def test_bad_login_response_code(self, mock_post, mock_connect, mock_json,
                                     mock_file):
        with self.assertRaises(RuntimeError):
            self.loop.run_until_complete(self.client.login())
        mock_connect.assert_called_with(
            'ws://sim.smogon.com:8000/showdown/websocket')
        mock_post.assert_called_with(
            'https://play.pokemonshowdown.com/action.php',
            data={
                'act': 'login',
                'name': 'uname',
                'pass': 'pass',
                'challstr': '1|1'
            })

    @patch('psclient.psclient.open')
    @patch('json.load', return_value={'username': 'uname', 'password': 'pass'})
    @patch('websockets.connect',
           new_callable=AsyncMock,
           return_value=AsyncMock(recv=AsyncMock(return_value='|challstr|1|1'))
           )
    @patch('requests.post',
           return_value=Mock(
               status_code=200,
               text=']{"actionsuccess": false,"assertion":"assertion"}',
               content=''))
    def test_bad_login_response_value(self, mock_post, mock_connect, mock_json,
                                      mock_file):
        with self.assertRaises(RuntimeError):
            self.loop.run_until_complete(self.client.login())
        mock_connect.assert_called_with(
            'ws://sim.smogon.com:8000/showdown/websocket')
        mock_post.assert_called_with(
            'https://play.pokemonshowdown.com/action.php',
            data={
                'act': 'login',
                'name': 'uname',
                'pass': 'pass',
                'challstr': '1|1'
            })

    def test_send_packed_team(self):
        m = mock_open(read_data=self.packed_team)
        with patch('psclient.psclient.open', m):
            self.client.load_team('gen8ou', '', True)
        self.assertEqual(self.client.teams['gen8ou'], self.packed_team)

    def test_send_pokepaste_team(self):
        m = mock_open(read_data=self.pokepaste)
        with patch('psclient.psclient.open', m):
            self.client.load_team('gen8ou', '')
        self.assertEqual(self.client.teams['gen8ou'], self.packed_team)
