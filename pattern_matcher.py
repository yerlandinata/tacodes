import re

HYPERNYM_TAG = '<hypernym>'
HYPONYM_TAG = '<hyponym>'

class PatternMatcher:

    def __init__(self, pattern_src):
        self.patterns = []
        self.original_patterns = dict()
        with open(pattern_src, 'r') as f:
            for line in f:
                tokens = []
                for token in line:
                    if token == HYPERNYM_TAG or token == HYPONYM_TAG:
                        tokens.append(re.compile(r'([a-zA-Z\_]+)\/(?:NN)(?!(?:[A-Z]))'))
                    else:
                        tokens.append(re.compile(token + r'\/[A-Z]+'))
                    self.original_patterns[tokens[-1]] = line

        self.patterns.sort(reverse=True)
    
    def match(self, postagged):
        for p in self.patterns:
            match_obj = self.regex_pattern.search(tagged)
            if match_obj is not None:
                return match_obj.group(1), match_obj.group(2), self.original_patterns[p]
        return None, None, None
