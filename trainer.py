"""
The trainer module handles everything related to getting
training data and developing the model
"""
import urllib.request

def get_training_data(format: str):
    url = f'https://replay.pokemonshowdown.com/search?output=html&rating&format={format}'
    with urllib.request.urlopen(url) as response:
        print(response.read())
