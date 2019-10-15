import time
import os
import json
import pandas as pd
from selenium import webdriver
from dotenv import load_dotenv
from urllib.parse import urlsplit, parse_qs

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
# elif len(rows) > 1:
#     print('ambiguous: ', list(rows.synset_id))
#     exit()

try:
    existing_tree = os.environ.get('EXISTING_TREE')
    nodes = json.load(open(existing_tree, 'r'))
    print('existing hypernymy detected!')
except:
    nodes = dict()

driver = webdriver.Firefox()

def scrape_hypernyms(synset_id, child=None):
    print('-------------------------')
    driver.get(BASE_URL + '&synset=' + synset_id)
    indon = 'n/a'

    try:
        indon = driver.find_element_by_xpath('/html/body/table[1]/tbody/tr[2]/td[2]').text
        print('term:', indon)
    except:
        print('no indonesian translation')
    finally:
        print('synset_id:', synset_id)

    # new concept already exists in our DB
    if synset_id in nodes.keys():
        # check if the child concept is not already the hyponym of this concept
        if child['synset_id'] not in nodes[synset_id]['children']:
            nodes[synset_id]['children'].append(child['synset_id'])
        print('concept already exist in DB')
        return

    child = {
        'synset_id': synset_id,
        'word': indon,
        'children': [child['synset_id']] if child is not None else []
    } 
    nodes[synset_id] = child

    hypernyms_elements = []
    try:
        hypernym_label = driver.find_element_by_xpath('/html/body/table[2]/tbody/tr[2]/td[1]/strong')
        if 'hypernym' not in hypernym_label.text.lower():
            print('no hypernym')
            return
        hypernyms_elements = driver.find_elements_by_xpath("/html/body/table[2]/tbody/tr[2]/td[2]/a")
    except:
        print('no hypernym')
        return
    
    hypernyms = []
    for element in hypernyms_elements:
        try:
            url = element.get_attribute('href')
            query = urlsplit(url).query
            params = parse_qs(query)
            hypernyms.append(params['synset'][0])
        except:
            pass

    for hypernym in hypernyms:
        scrape_hypernyms(hypernym, child)

scrape_hypernyms(rows.synset_id.iloc[0])

driver.quit()

output_file = os.environ.get('OUTPUT_FILE')

with open(output_file, 'w') as f:
    f.write(json.dumps(nodes))
