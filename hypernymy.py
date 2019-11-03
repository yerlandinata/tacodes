import re
import os
import subprocess
from .corpus import CorpusEntry
from .lexicon import Lexicon
from nltk.tokenize import word_tokenize

HYPERNYM_TAG = '<hypernym>'
HYPONYM_TAG = '<hyponym>'
ANY_TAG = '<any>'
COPULA_TAG = '<copula>'
TYPE_TAG = '<type>'
ANY_NON_NOUN_TAG = '<not noun>'
COPULA_PATTERN = r'[a-z]+\/Kopula'
TYPE_PATTERN = r'[a-z]+\/Jenis(?: dari\/Preposisi)*'
ANY_PATTERN = r'[a-zA-Z\_]+\/[A-Z][a-z]*'
ANY_NON_NOUN_PATTERN = r'[a-zA-Z\_]+\/(?:(?!(?:Nomina| )).)*'
INSTANCE_CAPTURE = r'([a-zA-Z\_]+)\/(?:Nomina)(?!(?:[A-Z]))'
ALPHABETS_ONLY = re.compile(r'^[a-zA-Z\_]+$')
FAMRASHEL_POSTAG = re.compile(r'\/[A-Z]+\,*[A-Z]*')
# space is used for MWEs

with open('lexicon/hypernym_ignore.txt', 'r') as f:
    HYPERNYM_IGNORE = f.read().split('\n')

def pos_tag(s, tagger_dir='indonesian-postag'):
    wd = os.getcwd()
    os.chdir(tagger_dir)
    result = subprocess.check_output(['bash', 'tag.sh', '-raw', s])
    os.chdir(wd)
    result = result.decode().replace('\t', '/').replace('\n', ' ')
    return result.replace('  ', ' ')

def morph_tag(s):
    read, write = os.pipe()
    s = ' '.join(word_tokenize(s))
    os.write(write, s.encode())
    os.close(write)
    result = subprocess.check_output(['perl', 'morphind/MorphInd.pl'], stdin=read)
    tagged = []
    for w, m in zip(s.split(), result.decode().split()):
        try:
            tag = m[-4]
        except:
            return ''
        tagged.append(w + '/' + tag)
    res = ' '.join(tagged)
    return res

class HypernymyRelation:
    
    def __init__(self, hypernym, hyponym, source=None):
        self.hypernym = hypernym
        self.hyponym = hyponym
        self.source = source

    def from_dump(dump_str):
        pair, source = dump_str.split('<-')
        pair = pair.strip()[1:-1]
        source = source.strip()
        hypernym, hyponym = pair.split(', ')
        return HypernymyRelation(hypernym, hyponym, source=source)

        
    def __str__(self):
        return '({}, {})'.format(self.hypernym, self.hyponym) + (' <- {}'.format(self.source) if self.source else '')
    
    def __repr__(self):
        return self.__str__()
    
    def __hash__(self):
        return hash(self.hypernym) ^ hash(self.hyponym)
    
    def __eq__(self, other):
        return self.hypernym == other.hypernym and self.hyponym == other.hyponym
    
    def __ne__(self, other):
        return not self.__eq__(other)

class HypernymyPattern:
    
    def __init__(self, pattern):
        self.group = []
        pattern = pattern.strip().lower()
        for word in pattern.split():
            if HYPERNYM_TAG in word:
                self.group.append(HYPERNYM_TAG)
            elif HYPONYM_TAG in word:
                self.group.append(HYPONYM_TAG)
        self.pattern = pattern
        self.regex_pattern = self.build_regex_pattern(pattern)
    
    def build_regex_pattern(self, pattern):
        result = ''
        for token in pattern.split(' '):
            if ALPHABETS_ONLY.match(token):
                result += token
                result += '\/[A-Z][a-z]*'
            else:
                result += token
            result += ' '
        result = result.strip()
        result = result.replace(HYPERNYM_TAG, INSTANCE_CAPTURE)
        result = result.replace(HYPONYM_TAG, INSTANCE_CAPTURE)
        result = result.replace(ANY_TAG, ANY_PATTERN)
        result = result.replace(ANY_NON_NOUN_TAG, ANY_NON_NOUN_PATTERN)
        result = result.replace(COPULA_TAG, COPULA_PATTERN)
        result = result.replace(TYPE_TAG, TYPE_PATTERN)
        return re.compile(result)

    def match(self, entry, is_entry_postagged=False):
        if is_entry_postagged:
            tagged = entry.get_sentence()
        else:
            tagged = entry.get_lexical_class_tagged()
        match_obj = self.regex_pattern.search(tagged)
        if match_obj is not None:
            hypernyms = []
            hyponyms = []
            for i in range(len(self.group)):
                instance = match_obj.group(i+1)
                if self.group[i] == HYPERNYM_TAG:
                    hypernyms.append(instance)
                else:
                    hyponyms.append(instance)
            hypernymies = []
            for hypernym in hypernyms:
                if hypernym not in HYPERNYM_IGNORE:
                    for hyponym in hyponyms:
                        if hypernym != hyponym:
                            hypernymies.append(HypernymyRelation(hypernym, hyponym, source=entry))
            return hypernymies
        return []
    
    def __str__(self):
        return self.pattern
    
    def __repr__(self):
        return self.__str__()
    
    def __hash__(self):
        return hash(self.pattern)
    
    def __eq__(self, other):
        return self.pattern == other.pattern
    
    def __ne__(self, other):
        return self.pattern != other.pattern