import re

HYPERNYM_TAG = '<hypernym>'
HYPONYM_TAG = '<hyponym>'

class PatternMatcher:

    def __init__(self, pattern_src):
        self.patterns = []
        self.original_patterns = dict()
        ori_patterns = []
        with open(pattern_src, 'r') as f:
            for line in f:
                ori_patterns.append(line)

        ori_patterns = sorted(ori_patterns, key=lambda p: -p.count(' '))

        for p in ori_patterns:
            tokens = []
            for token in p:
                if token == HYPERNYM_TAG or token == HYPONYM_TAG:
                    tokens.append(('([a-zA-Z\s]+)\/(?:NN)(?!(?:[A-Z]))'))
                else:
                    tokens.append(token + r'\/[A-Z]+')
                self.original_patterns[tokens[-1]] = p
            self.patterns.append(re.compile(' '.join(tokens)))

    
    def match(self, postagged):
        for p in self.patterns:
            match_obj = self.regex_pattern.search(tagged)
            if match_obj is not None:
                return match_obj.group(1), match_obj.group(2), self.original_patterns[p]
        return None, None, None
