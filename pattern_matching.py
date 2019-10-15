import os
import re
import time
import json
import multiprocessing
import datetime
import numpy as np
from collections import Counter
from hypernymy import HypernymyRelation, HypernymyPattern, morph_tag
from corpus import WikipediaCorpus, WikipediaCorpusEntry

print('Pattern Matching\n--------------------')

hypernymy_patterns = []

with open('hypernymy_pattern_v8.txt', 'r') as f:
    for p in f.readlines():
        hypernymy_patterns.append(HypernymyPattern(p))

hypernymy_patterns = sorted(hypernymy_patterns, key=lambda p: -len(p.pattern))

print('loading corpus...', end='')
corpus = WikipediaCorpus()
print('\rloaded!')
manager = multiprocessing.Manager()
collected_pairs = manager.dict({str(p): [] for p in hypernymy_patterns})

EXPERIMENT_NAME = '_v8_nounfilter'
NUM_OF_WORKERS = 7

process = []
collected_pairs_count = manager.Value('i', 0)
processed_entries = manager.Value('i', 0)
write_lock = manager.Lock()
entries = corpus.get_all_entries()
BUFFER_SIZE = 1000

def process_entries(begin, end):
    global collected_pairs_count
    global processed_entries
    local_collected_pairs = {str(p): [] for p in hypernymy_patterns}
    local_processed_entries = 0
    local_pairs_count = 0
    for i in range(begin, end):
        for pattern in hypernymy_patterns:
            pairs = pattern.match(entries[i])
            local_pairs_count += len(pairs)
            local_collected_pairs[str(pattern)] += pairs
            if len(pairs) > 0:
                break
        local_processed_entries += 1
        if i % BUFFER_SIZE == 0:
            write_lock.acquire()
            collected_pairs_count.value += local_pairs_count
            processed_entries.value += local_processed_entries
            for p in hypernymy_patterns:
                collected_pairs[str(p)] += local_collected_pairs[str(p)]
            write_lock.release()
            local_collected_pairs = {str(p): [] for p in hypernymy_patterns}
            local_processed_entries = 0
            local_pairs_count = 0
    write_lock.acquire()
    collected_pairs_count.value += local_pairs_count
    processed_entries.value += local_processed_entries
    for p in hypernymy_patterns:
        collected_pairs[p] += local_collected_pairs[p]
    write_lock.release()
        
def worker_watcher():
    start_time = datetime.datetime.now()
    target = len(corpus)
    while True:
        elapsed_time = str(datetime.datetime.now() - start_time).split('.')[0]
        print(
            'Entries: {}/{} | pairs: {} | {}'.format(
                processed_entries.value, target, collected_pairs_count.value, elapsed_time
            ), end='\r', flush=True
        )
        if processed_entries.value == target:
            with open('{}_experiment{}.json'.format(int(time.time()), EXPERIMENT_NAME), 'w') as f:
                json.dump(
                    {pattern: sorted([str(pair) for pair in collected_pairs[pattern]]) for pattern in collected_pairs.keys()}, f
                )
            break
        time.sleep(10)
        
def execute():
    global process
    i = 0
    t = 0
    threads = []
    for t in range(NUM_OF_WORKERS - 1):
        proc = multiprocessing.Process(target=process_entries, args=(i, i+(len(entries)//NUM_OF_WORKERS),))
        process.append(proc)
        proc.start()
        i += (len(entries) // NUM_OF_WORKERS)
    proc = multiprocessing.Process(target=process_entries, args=(i, len(entries), ))
    process.append(proc)
    proc.start()
    watcher = multiprocessing.Process(target=worker_watcher)
    process.append(watcher)
    watcher.start()

execute()