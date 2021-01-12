"""
The trainer module handles everything related to getting
training data and developing the model
"""
import requests
import logging
import time
import os
from html.parser import HTMLParser

logger = logging.getLogger(__name__)

class ReplayListParser(HTMLParser):
    replay_links = list()

    def handle_starttag(self, starttag, attrs):
        if starttag == 'a':
            for name, data in attrs:
                if name == 'href':
                    self.replay_links.append(data)

def get_training_data(format: str):
    base_url = 'https://replay.pokemonshowdown.com'
    search_url = '/search/?output=html&rating&format={0}&page={1}'
    replay_dir = f'./data/{int(time.time())}'
    end_of_replays = False
    page = 1
    
    if not os.path.exists(replay_dir):
        os.makedirs(replay_dir)
    logger.info(f'Writing logs to {replay_dir}')

    while not end_of_replays:
        parser = ReplayListParser()
        logger.info('made request to ' +
                base_url + search_url.format(format, page))
        parser.feed(requests.get(base_url + search_url.format(format, page)).text)
        if len(parser.replay_links) == 0:
            break;
        for replay in parser.replay_links:
            with open(replay_dir + replay + '.log', 'w') as file:
                file.write(requests.get(base_url + replay + '.log').text)
        page += 1

