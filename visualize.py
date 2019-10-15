import json
import os
from graphviz import Digraph
from dotenv import load_dotenv
import graph_algorithm

load_dotenv(dotenv_path='visualization.env')

nodes = json.load(open(os.environ.get('INPUT_TREE'), 'r'))

graph = Digraph(comment='The Semantic Hierarchy')
graph.attr(rankdir='BT')

graph_algorithm.prune_graph(nodes, os.environ.get('PRUNING'))
root_synset = graph_algorithm.find_root_synset(nodes)

print(nodes[root_synset])
graph.node(root_synset, nodes[root_synset]['word'])
graph.attr(rank='max')

for synset_id in nodes.keys():
    if synset_id != root_synset:
        graph.node(synset_id, nodes[synset_id]['word'])

for synset_id in nodes.keys():
    for child_synset_id in nodes[synset_id]['children']:
        graph.edge(child_synset_id, synset_id)

graph.render('hierarchy.gv', view=True)
