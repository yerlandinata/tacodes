import string
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

STEMMER = StemmerFactory().create_stemmer()
PUNCTUATION = string.punctuation.replace('_', '').replace('-', '')

def stem(word):
    if '_' in word: # MWE
        return word.lower()
    return STEMMER.stem(word)

def stem_if_not_noun(lexicon, word):
    try:
        lexicon_entry = lexicon.get_entry(word)
    except KeyError:
        return word.lower()
    if lexicon_entry.pos != 'Nomina' and lexicon_entry.lemma is not None:
        return lexicon_entry.lemma
    return word.lower()

def is_valid_mwe(word):
    count_non_alphas = len([c for c in word if not c.isalpha()])
    is_alphas_dominant = len(word) > 3 * count_non_alphas
    has_digit = any(c.isdigit() for c in word)
    has_strange_char = any(c in PUNCTUATION for c in word)
    return not has_digit and not has_strange_char and is_alphas_dominant

def is_valid_word(word):
    if '//' in word:
        return False
    count_punc = len([c for c in word if c in string.punctuation])
    count_digit = len(list(filter(str.isdigit, word)))
    count_alpha = len(list(filter(str.isalpha, word)))
    return (len(word) > 5 * count_punc or count_punc == 1) and (count_alpha * count_digit == 0 or count_digit == 1)
