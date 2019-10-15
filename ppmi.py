import datetime
import json
import math
import os
import sys
import numpy as np
from collections import Counter
from scipy import sparse
from .cleaner import stem

class PPMI:

    TOKEN_TO_INDEX_DUMP = 'token_to_index.json'
    INDEX_TO_TOKEN_DUMP = 'index_to_token.json'
    SKIPGRAM_COUNT_DUMP = 'skipgram.json'
    WORD_WORD_SPARSE_DUMP = 'wwcnt_sparse.npz'
    PPMI_DUMP = 'ppmi_sparse.npz'
    UNIGRAM_COUNT_DUMP = 'unigram.json'

    def __init__(self, window_size=5, work_dir=None, verbose=False, stemmer=stem):
        if work_dir is not None and work_dir[-1] != '/':
            work_dir += '/'
        self.__wd = work_dir
        self.is_verbose = verbose
        self.__start_time = None
        self.__window_size = window_size
        self.__stem = stem
        if work_dir is not None:
            with open(self.__wd + PPMI.TOKEN_TO_INDEX_DUMP, 'r') as f:
                self.__tok2indx = json.load(f)
            with open(self.__wd + PPMI.INDEX_TO_TOKEN_DUMP, 'r') as f:
                self.__indx2tok = json.load(f)
            if PPMI.PPMI_DUMP in os.listdir(work_dir):
                self.__ppmi_mat = sparse.load_npz(self.__wd + PPMI.PPMI_DUMP)

    def verbose(self, *args):
        if self.is_verbose:
            info = ' '.join(list(map(str, args)))
            print(
                '\r',
                info,
                ' | elapsed: {}'.format(
                    str(datetime.datetime.now() - self.__start_time).split('.')[0]
                ) if self.__start_time is not None else '',
                ' ' * 100,
                end='', flush=True
            )

    def fit(self, corpus, work_dir='ppmi/'):
        self.__start_time = datetime.datetime.now()
        if work_dir is not None:
            self.__wd = work_dir
        existing_works = os.listdir(self.__wd)
        if PPMI.TOKEN_TO_INDEX_DUMP not in existing_works or PPMI.INDEX_TO_TOKEN_DUMP not in existing_works:
            self.__process_unigram(corpus)
            self.__process_skipgram(corpus)
            self.__create_word_word_count_sparse_matrix()
            self.__compute_ppmi_matrix()
        else:
            with open(self.__wd + PPMI.TOKEN_TO_INDEX_DUMP, 'r') as f:
                self.__tok2indx = json.load(f)
            with open(self.__wd + PPMI.INDEX_TO_TOKEN_DUMP, 'r') as f:
                self.__indx2tok = json.load(f)
            if PPMI.SKIPGRAM_COUNT_DUMP not in existing_works:
                self.__process_skipgram(corpus)
                self.__create_word_word_count_sparse_matrix()
                self.__compute_ppmi_matrix()
            else:
                with open(self.__wd + PPMI.SKIPGRAM_COUNT_DUMP, 'r') as f:
                    self.verbose('Loading existing skipgrams..')
                    self.__skipgram_counts = json.load(f)
                if PPMI.WORD_WORD_SPARSE_DUMP not in existing_works:
                    self.__create_word_word_count_sparse_matrix()
                    self.__compute_ppmi_matrix()
                else:
                    self.__wwcnt_mat = sparse.load_npz(self.__wd + PPMI.WORD_WORD_SPARSE_DUMP)
                    if PPMI.PPMI_DUMP not in existing_works:
                        self.__compute_ppmi_matrix()
                    else:
                        self.__ppmi_mat = sparse.load_npz(self.__wd + PPMI.PPMI_DUMP)

    def __process_unigram(self, corpus):
        '''
        Process unigram so they can be encoded eficiently
        '''
        self.verbose('Begin processing unigram...')
        unigram_counts = Counter()
        for ii, entry in enumerate(corpus.get_all_entries()):
            if ii % 200000 == 0:
                self.verbose('Unigram:', ii, 'corpus entries processed')
            for token in entry.get_sentence().split():
                unigram_counts[token] += 1
        self.__tok2indx = dict()
        self.__indx2tok = []
        for token, count in unigram_counts.most_common():
            self.__tok2indx[token] = len(self.__indx2tok)
            self.__indx2tok.append(token)
        with open(self.__wd + PPMI.UNIGRAM_COUNT_DUMP, 'w') as f:
            json.dump(unigram_counts, f)
        del unigram_counts
        with open(self.__wd + PPMI.TOKEN_TO_INDEX_DUMP, 'w') as f:
            json.dump(self.__tok2indx, f)
        with open(self.__wd + PPMI.INDEX_TO_TOKEN_DUMP, 'w') as f:
            json.dump(self.__indx2tok, f)
        self.verbose('Done processing unigram!')

    def __process_skipgram(self, corpus):
        '''
        Find all skipgrams and save
        '''
        self.verbose('Begin processing skipgram...')
        self.__skipgram_counts = Counter()
        for i, entry in enumerate(corpus.get_all_entries()):
            sentence_tokenized  = entry.get_sentence().split()
            for ifw, fw in enumerate(sentence_tokenized):
                icw_min = max(0, ifw - self.__window_size)
                icw_max = min(len(sentence_tokenized) - 1, ifw + self.__window_size)
                icws = [ii for ii in range(icw_min, icw_max + 1) if ii != ifw]
                for icw in icws:
                    skipgram = (sentence_tokenized[ifw], sentence_tokenized[icw])
                    encoded_skipgram = self.encode_skipgram(skipgram)
                    self.__skipgram_counts[encoded_skipgram] += 1    
            if i % 20000 == 0:
                self.verbose(
                    'Skipgram:', i, 'corpus entries processed', ' | Skipgram memory usage:', sys.getsizeof(self.__skipgram_counts) / (1 << 20), 'MB'
                )
        with open(self.__wd + PPMI.SKIPGRAM_COUNT_DUMP, 'w') as f:
            json.dump(self.__skipgram_counts, f)        

    def __create_word_word_count_sparse_matrix(self):
        '''
        Create a word-word count matrix
        '''
        row_indxs = []
        col_indxs = []
        dat_values = []
        ii = 0
        total_skipgrams = len(self.__skipgram_counts)
        for skipgram_encoded, sg_count in self.__skipgram_counts.items():
            ii += 1
            if ii % 1000000 == 0:
                self.verbose('Sparse:', ii, '/', total_skipgrams, 'skipgrams processed')
            tok1, tok2 = self.decode_skipgram(skipgram_encoded)
            tok1_indx = self.encode_token(tok1)
            tok2_indx = self.encode_token(tok2)
                
            row_indxs.append(tok1_indx)
            col_indxs.append(tok2_indx)
            dat_values.append(sg_count)
            
        self.verbose('Saving sparse matrix...')
        self.__wwcnt_mat = sparse.csr_matrix((dat_values, (row_indxs, col_indxs)))
        sparse.save_npz(self.__wd + PPMI.WORD_WORD_SPARSE_DUMP, self.__wwcnt_mat)
        self.verbose('Sparse matrix saved')

    def __compute_ppmi_matrix(self):
        '''
        Compute PPMI matrix in sparse format
        '''
        num_skipgrams = self.__wwcnt_mat.sum()

        # for creating sparce matrices
        row_indxs = []
        col_indxs = []

        ppmi_dat_values = []

        sum_over_words = np.array(self.__wwcnt_mat.sum(axis=0)).flatten()
        sum_over_contexts = np.array(self.__wwcnt_mat.sum(axis=1)).flatten()

        # we do not need this anymore from now on
        del self.__wwcnt_mat

        ii = 0
        total_skipgrams = len(self.__skipgram_counts)

        for skipgram_encoded, sg_count in self.__skipgram_counts.items():
            ii += 1
            if ii % 1000000 == 0:
                self.verbose('PPMI:', ii, '/', total_skipgrams, 'skipgrams processed')

            tok1, tok2 = self.decode_skipgram(skipgram_encoded)
            tok1_indx = self.encode_token(tok1)
            tok2_indx = self.encode_token(tok2)
            
            nwc = sg_count
            Pwc = nwc / num_skipgrams
            nw = sum_over_contexts[tok1_indx]
            Pw = nw / num_skipgrams
            nc = sum_over_words[tok2_indx]
            Pc = nc / num_skipgrams

            pmi = np.log2(Pwc/(Pw*Pc))
            ppmi = max(pmi, 0)

            row_indxs.append(tok1_indx)
            col_indxs.append(tok2_indx)
            ppmi_dat_values.append(ppmi)

        # we do not need this too from now on
        del self.__skipgram_counts

        self.verbose('Saving ppmi sparse matrix...')
        self.__ppmi_mat = sparse.csr_matrix((ppmi_dat_values, (row_indxs, col_indxs)))
        sparse.save_npz(self.__wd + PPMI.PPMI_DUMP, self.__ppmi_mat)
        self.verbose('Saved ppmi sparse matrix.')

    def get_ppmi(self, w1, w2):
        encoded_w1 = self.encode_token(self.__stem(w1))
        encoded_w2 = self.encode_token(self.__stem(w2))
        return self.__ppmi_mat[encoded_w1,encoded_w2]

    def encode_token(self, token):
        try:
            return self.__tok2indx[token]
        except KeyError:
            raise KeyError('Unseen token: ' + token)

    def decode_token_index(self, idx):
        try:
            return self.__indx2tok[idx]
        except KeyError:
            raise KeyError('Unseen token: ' + token)

    def encode_skipgram(self, skipgram):
        w1, w2 = skipgram
        encoded_w1 = hex(self.encode_token(w1))[2:]
        encoded_w2 = hex(self.encode_token(w2))[2:]
        return encoded_w1 + '.' + encoded_w2

    def decode_skipgram(self, encoded):
        try:
            encoded_w1, encoded_w2 = encoded.split('.')
            encoded_w1 = int(encoded_w1, base=16)
            encoded_w2 = int(encoded_w2, base=16)
        except:
            raise ValueError('Invalid encoded skipgram: ' + encoded)
        return self.decode_token_index(encoded_w1), self.decode_token_index(encoded_w2)
