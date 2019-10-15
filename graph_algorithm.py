import graphviz
from wikipedia_service import wikipedia_service

WIKIDATA_PRUNING = 'wikidataprune'

class Concept:
    def __init__(self, concept_id=None, concept_term=None):
        self.id = concept_id
        self.term = concept_term

    def __str__(self):
        return '{}: {}'.format(self.id, self.term)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        try:
            return self.id == other.id
        except:
            return False
    
    def __ne__(self, other):
        return (not self.__eq__(other))

    def __hash__(self):
        return hash(self.id)

class Graph:
    def __init__(self, nodes):
        self.__nodes = set(nodes)
        self.__edge_list = {n: set() for n in nodes}

    def get_edge_list(self):
        return self.__edge_list

    def get_nodes(self):
        return set(self.__nodes)

    def remove_node_from_list(self, node):
        self.__nodes.remove(node)

class DirectedAcyclicGraph(Graph):

    def __init__(self, nodes):
        super().__init__(nodes)
        self.__edge_list_in = {n: set() for n in nodes}

    def get_edge_list_in(self):
        return self.__edge_list_in

    def get_edge_list_out(self):
        return self.get_edge_list()

    def get_node_level(self, node):
        level = 1
        current = node
        while True:
            parents = self.get_parents(current)
            if len(parents) == 0:
                break
            level += 1
            current = list(parents)[0]
        return level

    def get_parents(self, node):
        return set(self.get_edge_list_in()[node])

    def get_children(self, node):
        return set(self.get_edge_list_out()[node])

    def add_children(self, node, children):
        self.get_edge_list_out()[node].update(children)
        for child in children:
            self.get_edge_list_in()[child].add(node)

    def delete_edge(self, child, parent):
        self.get_edge_list_out()[parent].remove(child)
        self.get_edge_list_in()[child].remove(parent)

    def delete_node(self, node):
        if node not in self.get_nodes():
            return
        parents = self.get_parents(node)
        children = self.get_children(node)
        for parent in parents:
            self.get_edge_list_out()[parent].remove(node)
            self.add_children(parent, children)
        for child in children:
            self.get_edge_list_in()[child].remove(node)
        self.remove_node_from_list(node)
        
    def get_root(self):
        edge_list_in = self.get_edge_list_in()
        return {n for n in edge_list_in.keys() if len(edge_list_in[n]) == 0}

class ConceptGraph(DirectedAcyclicGraph):
    def __init__(self, concept_dict):
        nodes = []
        node_map = dict()
        for node_id in concept_dict.keys():
            node_raw = concept_dict[node_id]
            node = Node(Concept(concept_id=node_raw['synset_id'], concept_term=node_raw['word']))
            nodes.append(node)
            node_map[node_id] = node

        super().__init__(nodes)

        for node_id in concept_dict.keys():
            node = node_map[node_id]
            self.add_children(node, {node_map[child_id] for child_id in concept_dict[node_id]['children']})
        self.__node_map = node_map

    def render(self, filename='graph.gv'):
        digraph = graphviz.Digraph()
        nodes = self.get_nodes()

        for node in nodes:
            digraph.node(node.data.id, node.data.term)
            
        for node in nodes:
            for child in self.get_children(node):
                digraph.edge(node.data.id, child.data.id)
                
        digraph.render(filename)
        return digraph

class WikidataGraph(ConceptGraph):

    def prune(self):
        self.prune_mwe()
        self.prune_duplicate()
        self.prune_discourse()
        self.prune_loners()

    def prune_duplicate(self):
        unique_terms = set()
        duplicate_terms = set()
        for node in self.get_nodes():
            if node.data.term in unique_terms:
                duplicate_terms.add(node.data.term)
            unique_terms.add(node.data.term)
        for term in duplicate_terms:
            nodes = [node for node in self.get_nodes() if node.data.term == term]
            highest_node = nodes[0]
            highest_level = self.get_node_level(highest_node)
            for node in nodes[1:]:
                level = self.get_node_level(node)
                if level > highest_level:
                    highest_node = node
                    highest_level = level
            self.delete_node(highest_node)


    def prune_loners(self):
        for node in self.get_nodes():
            if len(self.get_parents(node)) + len(self.get_children(node)) == 0:
                self.remove_node_from_list(node)

    def prune_mwe(self):
        print('prune mwe...')
        for node in self.get_nodes():
            if node.data.term == 'n/a' or ' ' in node.data.term:
                self.delete_node(node)

    def prune_discourse(self):
        print('prune discourse...')
        for root in self.get_root():
            self.prune_discourse_recursive(root)

    def prune_discourse_recursive(self, node):
        print('prune discourse:', node)
        if node not in self.get_nodes():
            return
        for child in self.get_children(node):
            self.prune_discourse_recursive(child)
        new_parent = True
        while new_parent:
            new_parent = False
            for parent in self.get_parents(node):
                is_occur = False
                for term in (parent.data.term, node.data.term):
                    wiki_page = wikipedia_service.get_page_list(term)[0]
                    if len(wiki_page) < 4 * len(term): 
                        if wikipedia_service.is_term_cooccur(node.data.term, parent.data.term, wiki_page):
                            is_occur = True
                if not is_occur:
                    self.delete_edge(node, parent)
                    for grandparent in self.get_parents(parent):
                        self.add_children(grandparent, {node})
                    new_parent = True

class Node:
    def __init__(self, data):
        self.data = data
    
    def __eq__(self, other):
        try:
            return self.data == other.data
        except:
            return False
    
    def __ne__(self, other):
        return (not self.__eq__(other))

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return repr(self.data)

    def __hash__(self):
        return hash(self.data)

def find_root_synset(adjacency_list):
    root_synset = list(adjacency_list.keys())[0]
    while True:
        current_synset = root_synset
        for synset_id in adjacency_list.keys():
            for child_synset_id in adjacency_list[synset_id]['children']:
                if child_synset_id == root_synset:
                    root_synset = synset_id
                    break
        if current_synset == root_synset:
            print('root:', root_synset)
            return root_synset


