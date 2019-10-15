import string
from nltk.tokenize import word_tokenize
from nltk.util import ngrams

def is_valid_pos(pos):
    return ' ' not in pos and pos[0] in string.ascii_uppercase

class Lexicon():
    def __init__(self, db='lexicon/kateglo.txt', copula='lexicon/copula.txt', types='lexicon/types.txt'):
        self.__entries = dict()
        self.__pos = set()
        self.__copula = set()
        self.__types = set()
        with open(db, 'r') as f:
            for line in f.readlines():
                word, pos, lemma = line.split('\t')
                if not is_valid_pos(pos):
                    continue
                lemma = None if '-1' in lemma else lemma
                self.__entries[word] = LexiconEntry(word, pos, lemma)
                self.__pos.add(pos)
        with open(copula, 'r') as f:
            for line in f.readlines():
                self.__copula.add(line.strip())
        with open(types, 'r') as f:
            for line in f.readlines():
                self.__types.add(line.strip())

    def get_entry(self, word):
        return self.__entries[word].copy()

    def is_word_exists(self, word):
        return word in self.__entries.keys()

    def get_pos(self):
        return self.__pos.copy()

    def mwe_tokenize(self, sentence):
        unigram_tokenized = word_tokenize(sentence)
        tokenized = []
        mwe_found = False
        for bigram_head, bigram_tail in ngrams(unigram_tokenized, 2):
            if mwe_found:
                mwe_found = False
                continue
            bigram = bigram_head + ' ' + bigram_tail
            if self.is_word_exists(bigram.lower()):
                mwe_found = True
                tokenized.append(bigram)
            else:
                tokenized.append(bigram_head)
        if not mwe_found and len(unigram_tokenized) > 0:
            tokenized.append(unigram_tokenized[-1])
        return tokenized

    def tag_sentence(self, sentence):
        result = ''
        for token in self.mwe_tokenize(sentence):
            token = token.lower()
            result += token.replace(' ', '_')
            if token in string.punctuation:
                result += '/TandaBaca'
            elif token in self.__copula:
                result += '/Kopula'
            elif token in self.__types:
                result += '/Jenis'
            elif self.is_word_exists(token):
                result += '/' + self.get_entry(token).pos
            else:
                result += '/TakDikenal'
            result += ' '
        return result


class LexiconEntry():
    def __init__(self, word, pos, lemma):
        self.word = word.lower()
        self.lemma = lemma.lower() if lemma is not None else None
        self.pos = pos

    def copy(self):
        return LexiconEntry(self.word, self.pos, self.lemma)

    def __str__(self):
        return '{}/{}'.format(self.word, self.pos) + '/{}'.format(self.lemma) if self.lemma is not None else ''

    def __repr__(self):
        return self.__str__()
