import time
import os
import json
import pandas as pd
from selenium import webdriver
from dotenv import load_dotenv

load_dotenv(dotenv_path='wnbahasa.env')

WORDNET_DB = os.environ.get('WORDNET_DB')
BASE_URL = 'http://compling.hss.ntu.edu.sg/omw/cgi-bin/wn-gridx.cgi?usrname=&gridmode=wnbahasa'

wordnet = pd.read_csv(WORDNET_DB, sep='\t', names=['synset_id', 'language', 'quality', 'word'])
wordnet = wordnet.query('(quality == "Y") and language == "B"')

query = input("input: ")

rows = wordnet.query('word == "{}"'.format(query))

if len(rows) == 0:
    print('not found')
    exit()
elif len(rows) > 1:
    print('ambiguous: ', list(rows.synset_id))
    exit()

try:
    existing_tree = os.environ.get('EXISTING_TREE')
    nodes = json.load(open(existing_tree, 'r'))
    print('existing hypernymy detected!')
except:
    nodes = dict()

if rows.synset_id.iloc[0] in nodes.keys():
    print('this concept already covered!')
    exit()

driver = webdriver.Firefox()
driver.get(BASE_URL + '&synset=' + rows.synset_id.iloc[0])

nodes[rows.synset_id.iloc[0]] = {
    'synset_id': rows.synset_id.iloc[0],
    'word': rows.word.iloc[0],
    'children': [],
}

session_synset_id = set()
prev_concept = nodes[rows.synset_id.iloc[0]]

while True:
    try:
        hypernym_label = driver.find_element_by_xpath('/html/body/table[2]/tbody/tr[2]/td[1]/strong')

        if 'hypernym' not in hypernym_label.text.lower():
            print('no hypernym')
            break

        driver.find_element_by_xpath('/html/body/table[2]/tbody/tr[2]/td[2]/a').click()

        indon = 'n/a'
        synset_id = 'n/a'

        try:
            indon = driver.find_element_by_xpath('/html/body/table[1]/tbody/tr[2]/td[2]').text
            print('hypernym:', indon)
            synset_id = driver.find_element_by_xpath('/html/body/font/b').text
            print('synset_id:', synset_id)
            print('--------------------')
        except:
            print('no indonesian translation')
            synset_id = driver.find_element_by_xpath('/html/body/font/b').text
            print('synset_id:', synset_id)
            print('--------------------')
        
        # wornet ntu bug: cyclic prevention
        if synset_id in session_synset_id:
            continue

        session_synset_id.add(synset_id)

        # new concept already exists in our DB
        if synset_id in nodes.keys():
            # check if the previous concept is not already the hyponym of this concept
            if prev_concept['synset_id'] not in nodes[synset_id]['children']:
                nodes[synset_id]['children'].append(prev_concept['synset_id'])
            print('concept already exist in DB')
            break
        prev_concept = {
            'synset_id': synset_id,
            'word': ','.join(indon.split(',')[:3]),
            'children': [prev_concept['synset_id']]
        } 
        nodes[synset_id] = prev_concept

    except KeyboardInterrupt:
        pass

driver.quit()

output_file = os.environ.get('OUTPUT_FILE')

with open(output_file, 'w') as f:
    f.write(json.dumps(nodes))
