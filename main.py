from codes.corpus import Corpus
from codes.ppmi import PPMI

corpus = Corpus(src='wikipedia-dump-compiled/wikicorpus_clean.tsv')
ppmi = PPMI(verbose=True)
ppmi.fit(corpus)
