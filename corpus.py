class Corpus:
    def __init__(self, lexicon, src='wikipedia-dump-compiled/wikicorpus.tsv'):
        self.__src = src
        self.__lexicon = lexicon

    def get_all_entries(self):
        return CorpusIterator(self.__src)

class CorpusIterator:
    def __init__(self, src):
        self.__src = open(src, 'r')

    def __iter__(self):
        return self

    def __next__(self):
        line = self.__src.readline()
        if line == '':
            raise StopIteration
        else:
            return CorpusEntry(line)

class CorpusEntry:
    def __init__(self, line):
        try:
            identifier, self.__sentence = line.split('\t')
        except ValueError:
            raise ValueError('Invalid entry: ' + line)
        self.__source_document = ' '.join(identifier.split('_')[:-1])
        self.__sentence_id = identifier.split('-')[-1]
        self.__lex_tagged = None

    def __str__(self):
        return '({}) {}'.format(self.get_id(), self.__sentence)

    def __repr__(self):
        return self.__str__()

    def get_sentence(self):
        return self.__sentence

    def get_id(self):
        return '{}: {}'.format(self.__source_document, self.__sentence_id)
    
    def get_lexical_class_tagged(self):
        if self.__lex_tagged is None:
            self.__lex_tagged = self.__lexicon.tag_sentence(self.__sentence)
        return self.__lex_tagged

    def get_source_document(self):
        return self.__source_document
