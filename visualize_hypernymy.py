import json
import os
from graphviz import Digraph
import graph_algorithm

graph = Digraph(comment='The Semantic Hierarchy')
# graph.attr(rankdir='BT')
graph.attr(rank='max')

pairs = []
words = set()

with open('../experiment_result/1570949254_ppmi5.txt', 'r') as f:
    while True:
        line = f.readline()
        if line == '':
            break
        hypernym, hyponym = line.split(',')
        pairs.append((hypernym, hyponym))
        words.add(hypernym)
        words.add(hyponym)

for word in words:
    graph.node(word, word)

for hypernym, hyponym in pairs:
    graph.edge(hypernym, hyponym)

graph.render('../experiment_result/hierarchy.gv', view=True)
