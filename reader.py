# Natural Language Toolkit: Plaintext Corpus Reader
#
# Copyright (C) 2001-2010 NLTK Project
# Author: Steven Bird <sb@ldc.upenn.edu>
#         Edward Loper <edloper@gradient.cis.upenn.edu>
#         Nitin Madnani <nmadnani@umiacs.umd.edu>
# URL: <http://www.nltk.org/>
# For license information, see LICENSE.TXT

"""
A reader for corpora that consist of plaintext documents.
"""

import codecs
import re

import nltk.data
from nltk.tokenize import *
from nltk.internals import deprecated

from nltk.corpus.reader.util import *
from nltk.corpus.reader.api import *
from gensim.utils import lemmatize
import json

from glob import iglob
from lxml.etree import XMLSyntaxError
from lxml import etree
from StringIO import StringIO
from os import listdir
from os.path import join as pathjoin

class SkippingCorpusView(StreamBackedCorpusView):
    def __init__(self, fileid, unique, block_reader, startpos=0, encoding='utf8'):
        super(SkippingCorpusView, self).__init__(fileid, block_reader=None, startpos=startpos, encoding=encoding)
        self._unique = unique
        self._block_reader = block_reader
        self._skipped = 0
        self._tell = -1

    def read_block(self, stream):
        if self._tell != stream.tell():
            self._skipped = 0
            
        tokens = self._block_reader(self._stream)
        self._tell = stream.tell()
        if not self._unique[self._current_blocknum + self._skipped]:
            self._skipped += 1
            tokens = []
        return tokens

def read_desc(stream, newlines_are_periods=True):
    line = stream.readline()
    if not line:
        return None
    jso = json.loads(line)
    if not newlines_are_periods:
        return jso['desc']
    return '\n'.join([re.sub(r"([^\n.!? ]\s*)$", r"\1.", line) if re.search(r"([^\n.!? ]\s*)$", line) else line for line in jso['desc'].split('\n')])

def read_x(stream, x):
    line = stream.readline()
    if not line:
        return None
    jso = json.loads(line)
    if x not in jso:
        return None
    return jso[x]

def read_X(stream, X):
    line = stream.readline()
    if not line:
        return None
    jso = json.loads(line)
    result = dict()
    for f in X:
        result[f] = jso[f]
    return result

def read_price(stream):
    sprice = read_x(stream, 'price')
    if sprice is not None:
        return int(re.findall(r'(\d+)', sprice)[-1])
    return None
    
def read_attrs(re_which, stream):
    line = stream.readline()
    if not line:
        return None
    jso = json.loads(line)
    a = [a for a in jso['attrs'] if re.match(re_which, a)]
    return a[0] if a else None


class Json100CorpusReader(CorpusReader):

    CorpusView = SkippingCorpusView
    def __init__(self, root, fileids, dedupe=None,
                 word_tokenizer=WordPunctTokenizer(),
                 sent_tokenizer=nltk.data.LazyLoader(
                     'tokenizers/punkt/english.pickle'),
                 encoding=None):
        """
        Construct a new plaintext corpus reader for a set of documents
        located at the given root directory.  Example usage:

            >>> root = '/...path to corpus.../'
            >>> reader = PlaintextCorpusReader(root, '.*\.txt')
        
        @param root: The root directory for this corpus.
        @param fileids: A list or regexp specifying the fileids in this corpus.
        @param word_tokenizer: Tokenizer for breaking sentences or
            paragraphs into words.
        @param sent_tokenizer: Tokenizer for breaking paragraphs
            into words.
        """
        CorpusReader.__init__(self, root, fileids, encoding)
        self._unique = dict()
        tmp = set()
        for f in self._fileids:
            self._unique[f] = []
            with self.open(f) as fh:
                while True:
                    x = read_x(fh, dedupe) if dedupe else fh.readline()
                    if not x:
                        break
                    self._unique[f].append(x not in tmp if dedupe else True)
                    tmp.add(x)
                        
        self._word_tokenizer = word_tokenizer
        self._sent_tokenizer = sent_tokenizer

    def __iter__(self):
        for doc in self.docs():
            yield [word for sent in doc for word in sent]
        # for f in self._fileids:
        #     with self.open(f) as fh:
        #         for line in fh.readlines():
        #             jso = json.loads(line)
        #             yield jso['desc'].lower().split()

    def raw(self, newlines_are_periods=False):
        """
        @return: the given file(s) as a single string.
        @rtype: C{list} of C{str}
        """
        gc = [];
        for f in self._fileids:
            with self.open(f) as fh:
                for keep in self._unique[f]:
                    desc = read_desc(fh, newlines_are_periods)
                    if keep:
                        gc.append(desc)
        return gc
    
    def words(self):
        """
        @return: the given file(s) as a list of words
            and punctuation symbols.
        @rtype: C{list} of C{str}
        """
        return concat([self.CorpusView(path, self._unique[fileid], \
                                       self._read_word_block, \
                                       encoding=enc) \
                       for (path, enc, fileid) \
                       in self.abspaths(None, True, True)])
            
    
    def sents(self):
        """
        @return: the given file(s) as a list of
            sentences or utterances, each encoded as a list of word
            strings.
        @rtype: C{list} of (C{list} of C{str})
        """
        if self._sent_tokenizer is None:
            raise ValueError('No sentence tokenizer for this corpus')
        return concat([self.CorpusView(path, self._unique[fileid], \
                                       self._read_sent_block, \
                                       encoding=enc) \
                       for (path, enc, fileid) \
                       in self.abspaths(None, True, True)])

    def price(self):
        return concat([self.CorpusView(path, self._unique[fileid], \
                                       lambda stream: [read_price(stream)], \
                                       encoding=enc) \
                       for (path, enc, fileid) \
                       in self.abspaths(None, True, True)])

    def field(self, x):
        return concat([self.CorpusView(path, self._unique[fileid], \
                                       lambda stream: [read_x(stream, x)], \
                                       encoding=enc) \
                       for (path, enc, fileid) \
                       in self.abspaths(None, True, True)])

    def fields(self, vOfw):
        return concat([self.CorpusView(path, self._unique[fileid], \
                                       lambda stream: [read_X(stream, vOfw)], \
                                       encoding=enc) \
                       for (path, enc, fileid) \
                       in self.abspaths(None, True, True)])

    def attrs_matching(self, which):
        return concat([self.CorpusView(path, self._unique[fileid], \
                                       self._read_attrs_block_functor(which), \
                                       encoding=enc) \
                       for (path, enc, fileid) \
                       in self.abspaths(None, True, True)])

    def docs(self):
        return concat([self.CorpusView(path, self._unique[fileid], \
                                       self._read_doc_block, \
                                       encoding=enc) \
                       for (path, enc, fileid) \
                       in self.abspaths(None, True, True)])

    def _read_word_block(self, stream):
        words = []
        words.extend(self._word_tokenizer.tokenize(read_desc(stream)))
        return words
    
    def _read_sent_block(self, stream):
        sents = []
        sents.extend([self._word_tokenizer.tokenize(sent)
                      for sent in self._sent_tokenizer.tokenize(read_desc(stream))])
        return sents

    def _read_attrs_block_functor(self, which):
        def f(stream):
            return [read_attrs(f.which, stream)]
        f.which = which
        return f

    def _read_doc_block(self, stream):
        return [self._read_sent_block(stream)]
    
