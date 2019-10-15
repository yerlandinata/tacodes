import string
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

STEMMER = StemmerFactory().create_stemmer()
PUNCTUATION = string.punctuation.replace('_', '')

def stem(word):
    if '_' in word: # MWE
        return word.lower()
    return STEMMER.stem(word)

def stem_if_not_noun(lexicon, word):
    try:
        lexicon_entry = lexicon.get_entry(word)
    except KeyError:
        return word
    if lexicon_entry.pos != 'Nomina' and lexicon_entry.lemma is not None:
        return lexicon_entry.lemma
    return word

def is_valid_word(word):
    count_alphas = 0
    has_digit = any(c.isdigit() for c in word)
    has_strange_char = any(c in PUNCTUATION for c in word)
    return not has_digit and not has_strange_char
