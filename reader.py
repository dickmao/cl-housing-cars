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
from tutorial import items

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
    # consider normalizing away bullets \u2022 and right apostrophes \u2019
    # jso['desc'] = unicode.normalize('NFC', jso['desc'])
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
    
def read_numbers(stream, X):
    line = stream.readline()
    if not line:
        return None
    jso = json.loads(line)
    result = dict()
    for f in X:
        if f in jso and jso[f] is not None:
            result[f] = int(re.findall(r'(\d+(?:\.\d*)?)', jso[f])[0])
        else:
            result[f] = None
    return result
    
def read_datetimes(stream, X):
    line = stream.readline()
    if not line:
        return None
    jso = json.loads(line)
    result = dict()
    for f in X:
        result[f] = dateutil.parser.parse(jso[f])
    return result
    
def read_coords(stream):
    coords = read_x(stream, 'coords')
    return tuple(float(x) if x is not None else None for x in coords)
    
def read_attrs(re_which, stream):
    line = stream.readline()
    if not line:
        return None
    jso = json.loads(line)
    a = [a for a in jso['attrs'] if re.match(re_which, a)]
    return a[0] if a else None


class Json100CorpusReader(CorpusReader):

    CorpusView = SkippingCorpusView
    def __init__(self, root, fileids, 
                 dedupe=None,
                 link_select=None,
                 exclude=set(),
                 word_tokenizer=WordPunctTokenizer(),
                 sent_tokenizer=nltk.data.LazyLoader(
                     'tokenizers/punkt/english.pickle'),
                 encoding=None):
        CorpusReader.__init__(self, root, fileids, encoding)
        self._unique = dict()
        tmp = set()
        for f in self._fileids:
            self._unique[f] = []
            with self.open(f) as fh:
                while True:
                    x = read_X(fh, [dedupe, "link", "id"]) if dedupe else fh.readline()
                    if not x:
                        break
                    # self._unique[f] is True, True, False, False, True... for each fileid
                    include = True
                    if include and link_select:
                        include = re.search(r"/{0}/".format(link_select), x['link'])
                    if dedupe:
                        if include:
                            include = x[dedupe] not in tmp
                        tmp.add(x[dedupe])
                    if include and exclude:
                        include = x['id'] not in exclude
                    self._unique[f].append(include)
                        
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

    def numbers(self, vOfw):
        return concat([self.CorpusView(path, self._unique[fileid], \
                                       lambda stream: [read_numbers(stream, vOfw)], \
                                       encoding=enc) \
                       for (path, enc, fileid) \
                       in self.abspaths(None, True, True)])

    def datetimes(self, vOfw):
        return concat([self.CorpusView(path, self._unique[fileid], \
                                       lambda stream: [read_datetimes(stream, vOfw)], \
                                       encoding=enc) \
                       for (path, enc, fileid) \
                       in self.abspaths(None, True, True)])

    def price(self):
        return concat([self.CorpusView(path, self._unique[fileid], \
                                       lambda stream: [read_price(stream)], \
                                       encoding=enc) \
                       for (path, enc, fileid) \
                       in self.abspaths(None, True, True)])

    def coords(self):
        return concat([self.CorpusView(path, self._unique[fileid], \
                                       lambda stream: [read_coords(stream)], \
                                       encoding=enc) \
                       for (path, enc, fileid) \
                       in self.abspaths(None, True, True)])

    def field(self, x):
        return concat([self.CorpusView(path, self._unique[fileid], \
                                       lambda stream: [read_x(stream, x)], \
                                       encoding=enc) \
                       for (path, enc, fileid) \
                       in self.abspaths(None, True, True)])

    def fields_all(self):
        return concat([self.CorpusView(path, self._unique[fileid], \
                                       lambda stream: [read_X(stream, items.DmozItem.fields.keys())], \
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
    
class BlogCorpusReader(CorpusReader):

    CorpusView = StreamBackedCorpusView

    def __iter__(self):
        for doc in self.docs():
            yield doc
        # for f in self._fileids:
        #     with self.open(f) as fh:
        #         buf = self._read_xml(fh)
        #         if len(buf.split()) != 0:
        #             yield buf.split()
        
    def __init__(self, root, fileids, 
                 word_tokenizer=WordPunctTokenizer(),
                 sent_tokenizer=nltk.data.LazyLoader(
                     'tokenizers/punkt/english.pickle'),
                 encoding=None):
        CorpusReader.__init__(self, root, fileids, encoding)
        self._fileids = [fileid for fileid in self._fileids if os.path.getsize(pathjoin(root, fileid)) < 20000]
        self._word_tokenizer = word_tokenizer
        self._sent_tokenizer = sent_tokenizer
        self._parser = etree.XMLParser(remove_blank_text=True,resolve_entities=False)

    def raw(self, fileids=None, sourced=False):
        """
        @return: the given file(s) as a single string.
        @rtype: C{str}
        """
        if fileids is None: fileids = self._fileids
        elif isinstance(fileids, basestring): fileids = [fileids]
        
        gc = '';
        for f in fileids:
            with self.open(f) as fh:
                while True:
                    desc = self._read_xml(fh)
                    if not desc:
                        break
                    gc = gc + desc
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
        return [x for x in res if x != []]
            
    def _read_doc_block(self, stream):
        doc = self._word_tokenizer.tokenize(self._read_xml(stream))
        return [doc]

    def _read_word_block(self, stream):
        words = []
        buf = self._read_xml(stream)
        words.extend(self._word_tokenizer.tokenize(buf))
        return words
    
    def _read_sent_block(self, stream):
        sents = []
        buf = self._read_xml(stream)
        sents.extend([self._word_tokenizer.tokenize(sent)
                      for sent in self._sent_tokenizer.tokenize(buf)])
        return sents

    def _read_xml(self, stream):
        what = ''
        x = ''.join(['<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd" >\n'] + stream.readlines())
        x = re.sub(r'&(?!\w+;)', '&amp;', x)
        try:
            r = etree.parse(StringIO(x),self._parser).getroot()
        except XMLSyntaxError:
            pass
        else:
            what = ''.join([post.text.encode('ascii', 'ignore') for post in r.findall('post')])
        return what.lower()
