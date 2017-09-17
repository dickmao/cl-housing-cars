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

def read_desc(stream, newlines_are_periods=False):
    line = stream.readline()
    if not line:
        return None
    jso = json.loads(line)
    if not newlines_are_periods:
        return jso['desc']
    return '\n'.join([re.sub(r"([^\n.!? ]\s*)$", r"\1.", line) if re.search(r"([^\n.!? ]\s*)$", line) else line for line in jso['desc'].split('\n')])

def read_link(stream):
    line = stream.readline()
    if not line:
        return None
    jso = json.loads(line)
    return jso['link']

def read_price(stream):
    line = stream.readline()
    if not line:
        return None
    jso = json.loads(line)
    return jso['price']

def read_coords(stream):
    line = stream.readline()
    if not line:
        return None
    jso = json.loads(line)
    return jso['coords']

def read_attrs(re_which, stream):
    line = stream.readline()
    if not line:
        return None
    jso = json.loads(line)
    a = [a for a in jso['attrs'] if re.match(re_which, a)]
    return a[0] if a else None


class Json100CorpusReader(CorpusReader):

    CorpusView = StreamBackedCorpusView
    def __init__(self, root, fileids,
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

    def raw(self, fileids=None, sourced=False, newlines_are_periods=False):
        """
        @return: the given file(s) as a single string.
        @rtype: C{list} of C{str}
        """
        if fileids is None: fileids = self._fileids
        elif isinstance(fileids, basestring): fileids = [fileids]
        
        gc = [];
        for f in fileids:
            with self.open(f) as fh:
                while True:
                    desc = read_desc(fh, newlines_are_periods)
                    if desc == None:
                        break
                    gc.append(desc)
        return gc
    
    def newlines_are_periods(self, fileids=None, sourced=False):
        """
        @return: the given file(s) as a single string.
        @rtype: C{list} of C{str}
        """
        if fileids is None: fileids = self._fileids
        elif isinstance(fileids, basestring): fileids = [fileids]
        
        gc = [];
        for f in fileids:
            with self.open(f) as fh:
                while True:
                    desc = read_desc(fh)
                    if desc == None:
                        break
                    gc.append(desc)
        return gc
    
    def words(self, fileids=None, sourced=False):
        """
        @return: the given file(s) as a list of words
            and punctuation symbols.
        @rtype: C{list} of C{str}
        """
        # Once we require Python 2.5, use source=(fileid if sourced else None)
        if sourced:
            return concat([self.CorpusView(path, self._read_word_block,
                                           encoding=enc, source=fileid)
                           for (path, enc, fileid)
                           in self.abspaths(fileids, True, True)])
        else:
            return concat([self.CorpusView(path, self._read_word_block,
                                           encoding=enc)
                           for (path, enc, fileid)
                           in self.abspaths(fileids, True, True)])
            
    
    def sents(self, fileids=None, sourced=False):
        """
        @return: the given file(s) as a list of
            sentences or utterances, each encoded as a list of word
            strings.
        @rtype: C{list} of (C{list} of C{str})
        """
        if self._sent_tokenizer is None:
            raise ValueError('No sentence tokenizer for this corpus')
        if sourced:
            return concat([self.CorpusView(path, self._read_sent_block,
                                           encoding=enc, source=fileid)
                           for (path, enc, fileid)
                           in self.abspaths(fileids, True, True)])
        else:
            return concat([self.CorpusView(path, self._read_sent_block,
                                           encoding=enc)
                           for (path, enc, fileid)
                           in self.abspaths(fileids, True, True)])

    def links(self, fileids=None, sourced=False):
        return concat([self.CorpusView(path, self._read_link_block,
                                       encoding=enc)
                       for (path, enc, fileid)
                       in self.abspaths(fileids, True, True)])

    def prices(self, fileids=None, sourced=False):
        return concat([self.CorpusView(path, self._read_price_block,
                                       encoding=enc)
                       for (path, enc, fileid)
                       in self.abspaths(fileids, True, True)])

    def coords(self, fileids=None, sourced=False):
        return concat([self.CorpusView(path, self._read_coords_block,
                                       encoding=enc)
                       for (path, enc, fileid)
                       in self.abspaths(fileids, True, True)])

    def attrs_matching(self, which, fileids=None, sourced=False):
        return concat([self.CorpusView(path, self._read_attrs_block_functor(which),
                                       encoding=enc)
                       for (path, enc, fileid)
                       in self.abspaths(fileids, True, True)])

    def docs(self, fileids=None, sourced=False):
        res = []
        if sourced:
            res = concat([self.CorpusView(path, self._read_doc_block,
                                           encoding=enc, source=fileid)
                           for (path, enc, fileid)
                           in self.abspaths(fileids, True, True)])
        else:
            res = concat([self.CorpusView(path, self._read_doc_block,
                                           encoding=enc)
                           for (path, enc, fileid)
                           in self.abspaths(fileids, True, True)])
        return res

    def _read_word_block(self, stream):
        words = []
        words.extend(self._word_tokenizer.tokenize(read_desc(stream)))
        return words
    
    def _read_sent_block(self, stream):
        sents = []
        sents.extend([self._word_tokenizer.tokenize(sent)
                      for sent in self._sent_tokenizer.tokenize(read_desc(stream))])
        return sents

    def _read_link_block(self, stream):
        return [read_link(stream)]

    def _read_price_block(self, stream):
        return [read_price(stream)]

    def _read_coords_block(self, stream):
        return [read_coords(stream)]

    def _read_attrs_block_functor(self, which):
        def f(stream):
            return [read_attrs(f.which, stream)]
        f.which = which
        return f

    def _read_doc_block(self, stream):
        return [self._read_sent_block(stream)]
    
