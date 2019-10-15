import time
import os
import json
from selenium import webdriver
from dotenv import load_dotenv

load_dotenv(dotenv_path='wikidata.env')

BASE_URL = 'https://www.wikidata.org/wiki/'

try:
    existing_tree = os.environ.get('EXISTING_TREE')
    nodes = json.load(open(existing_tree, 'r'))
    print('existing hypernymy detected!')
except:
    nodes = dict()

driver = webdriver.Firefox()

def scrape_hypernyms(synset_id, child=None):
    print('-------------------------')
    driver.get(BASE_URL + synset_id)
    indon = 'n/a'

    try:
        time.sleep(2)
        indon_label = driver.find_element_by_xpath('/html/body/div[3]/div[3]/div[4]/div/div[1]/div[1]/div[3]/table/tbody/tr[2]/th').text
        if indon_label != 'Indonesian':
            raise Exception()
        print('indonesian translation found!')
        indon = driver.find_element_by_xpath('/html/body/div[3]/div[3]/div[4]/div/div[1]/div[1]/div[3]/table/tbody/tr[2]/td[1]/div/div/span').text
        if indon == 'No label defined':
            indon = 'n/a'
            raise Exception()
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
        hypernyms_elements = driver.find_elements_by_xpath("//*[contains(text(), 'subclass of')]/../../../div[2]/div/div")
    except:
        print('no hypernym')
        return
    
    hypernyms = []
    for element in hypernyms_elements:
        try:
            hypernyms.append(element.find_element_by_xpath('div[2]/div[1]/div/div[2]/div[2]/div/a').get_attribute('title'))
        except:
            pass

    for hypernym in hypernyms:
        scrape_hypernyms(hypernym, child)

query = input("input wikidata document ID: ")
scrape_hypernyms(query)

driver.quit()

output_file = os.environ.get('OUTPUT_FILE')

with open(output_file, 'w') as f:
    f.write(json.dumps(nodes))
