import json
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='visualization.env')

nodes = json.load(open(os.environ.get('INPUT_TREE'), 'r'))

with open('data.js', 'w') as f:
    f.write('var graph = ' + json.dumps(nodes))
