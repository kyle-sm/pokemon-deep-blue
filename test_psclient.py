import unittest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from psclient import PSClient


class TestPSClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.get_event_loop()

    @classmethod
    def tearDownClass(cls):
        cls.loop.close()

    def setUp(self):
        self.client = PSClient()

    @patch('psclient.open')
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

    @patch('psclient.open')
    @patch('json.load', return_value={'username': 'uname', 'password': 'pass'})
    @patch('websockets.connect',
           new_callable=AsyncMock,
           return_value=AsyncMock(recv=AsyncMock(return_value='|challstr|1|1'))
           )
    @patch('requests.post', return_value=Mock(status_code=400, content=''))
    def test_bad_login_response_code(self, mock_post, mock_connect, mock_json,
                                     mock_file):
        with self.assertRaises(RuntimeError) as re:
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

    @patch('psclient.open')
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
        with self.assertRaises(RuntimeError) as re:
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
