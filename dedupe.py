#!/usr/bin/python

from __future__ import division
import os, errno, operator, re, sys, subprocess, signal, redis
import random
import numpy as np
import enchant
from nltk import bigrams,ConditionalFreqDist,FreqDist,pos_tag,pos_tag_sents
from gensim import parsing, matutils, interfaces, corpora, models, similarities, summarization
from gensim.utils import lemmatize
from nltk import collocations, association, text, tree
from gensim.corpora.mmcorpus import MmCorpus
from gensim.matutils import corpus2csc
from gensim.similarities.docsim import SparseMatrixSimilarity
from reader import Json100CorpusReader
import itertools, shutil, requests
from collections import Counter
from bisect import bisect_left

import re
from lxml import etree
from os import listdir
import json
from collections import defaultdict
from math import radians, sin, cos, sqrt, asin
from nltk.corpus.util import LazyCorpusLoader

from os import listdir
from os.path import getmtime, join, realpath
import dateutil.parser
from pytz import utc
from datetime import datetime
from dateutil.tz import tzlocal
import argparse

def argparse_dirtype(astring):
    if not os.path.isdir(astring):
        raise argparse.ArgumentError
    return astring

def get_index_of(id, lo=0, hi=None):
    hi = hi if hi is not None else len(ids)
    pos = bisect_left(ids, id, lo, hi)
    return (pos if pos != hi and ids[pos] == id else -1)

def make_dict():
    # corpora.Dictionary is a static method of gensim.corpora
    # it establishes the base of operations numbering the vocab,
    # and you feed it strings such as doc2bow(feedit) produces a sparse vector.

    # itertools.chain(*vOfv) produces a yielder of flattened docs (vOfw)
    # list(itertools.chain(*vOfv)) spells out the yield
    dictionary = corpora.Dictionary(list(craigcr))
    return dictionary

def datetime_parser(json_dict):
    for k,v in json_dict.iteritems():
        try:
            json_dict[k] = dateutil.parser.parse(v)
        except (ValueError, AttributeError):
            pass
    return json_dict

def determine_seven_day_fencepost(dt1):
    Markers = sorted([f for f in os.listdir(args.odir) if re.search(r'Marker\..*\.json$', f)],                      reverse=True)
    jsons = []
    for m in Markers:
        within = False
        with open(join(args.odir, m), 'r') as fp:
            url2dt = json.load(fp, object_hook=datetime_parser)
            for url,dt0 in url2dt.iteritems():
                if (dt1 - dt0).days < 7:
                    within = True
                    break
        if within:
            jsons.append("{}.{}.json".format(spider, m.split('.')[1]))
        else:
            break
    return jsons

class i2what(object):
    def __init__(self, arr):
        self._i2w = arr
    def __len__(self):
        return len(self._i2w)    
    def q_dupe(self, i):
        return self._i2w[i] < 0
    def __getitem__(self, i):
        return abs(self._i2w[i])
    def __iter__(self):
        for i in self._i2w:
            if self.q_dupe(i):
                next
            else:
                yield self[i]
        
def CorpusDedupe(cr, dict):
    # dict.doc2bow makes:
    #   corpus = [[(0, 1.0), (1, 1.0), (2, 1.0)],
    #             [(2, 1.0), (3, 1.0), (4, 1.0), (5, 1.0), (6, 1.0), (8, 1.0)],
    #             [(1, 1.0), (3, 1.0), (4, 1.0), (7, 1.0)],      ]
    corpus = [dict.doc2bow(doc) for doc in list(cr)]
    tfidf = models.TfidfModel(corpus)

    i2text = np.arange(1,len(corpus)+1,1)
    i2loc = np.arange(1,len(corpus)+1,1)
    index = SparseMatrixSimilarity(tfidf[corpus], num_features=len(dict.keys()))
    for i, z in enumerate(zip(index, coords)):
        if i2text[i] > 0:
            negated = -i2text[i]
            for j, sim in enumerate(z[0][i+1:]):
                if sim > .61:
		    i2text[i] = i2text[i+1+j] = negated
        if i2loc[i] > 0 and None not in z[1]:
            ci = z[1]
            negated = -i2loc[i]
            for j, cj in enumerate(coords[i+1:]):
                if ci == cj:
                    i2loc[i] = i2loc[i+1+j] = negated
    return i2what(i2text), i2what(i2loc)

def haversine(lat1, lon1, lat2, lon2):
    R = 6372.8 # Earth radius in kilometers
    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)

    a = sin(dLat/2)**2 + cos(lat1)*cos(lat2)*sin(dLon/2)**2
    c = 2*asin(sqrt(a))
 
    return R * c

def within(coords):
    if coords[0] is None or coords[1] is None:
	return False
    if spider == "dmoz":
	return coords[0] < 40.796126
    # que
    elif spider == "que":
	km = haversine(40.743924, -73.912388, float(coords[0]), float(coords[1]))
	return km < 4
    # sf
    elif spider == "sfc":
	km = haversine(37.779076, -122.397501, coords[0], coords[1])
	return km < 1.5
    # berkeley
    elif spider == "eby":
	km = haversine(37.871454, -122.298115, coords[0], coords[1])
	return km < 3
    # milbrae
    #    km = haversine(37.600122, -122.386914, coords[0], coords[1])
    # daly city
    #    km2 = haversine(37.687915, -122.472452, coords[0], coords[1]))
    return True


def qPronouns(vOfv):
    pronouns = re.compile("^(i|me|mine|our|he|she|they|their|we|my|his|her|myself|himself|herself|themselves)$", re.IGNORECASE)
    for w in [w for sent in vOfv for w in sent]:
	if pronouns.search(w):
	    return True
    return False


def nPara(raw):
    lines = raw.split('\n')
    wstart = next( (i for (i,l) in enumerate(lines) if re.search(r"\S", l) ), 0)
    wend = len(lines) - next( (i for (i,l) in enumerate(reversed(lines)) if re.search(r"\S", l) ), 0)
    result = 0
    inPara = False
    for l in lines[wstart:wend]:
        if re.search(r"\S", l):
            if not inPara:
                inPara = True
                result += 1
        elif inPara:
            inPara = False
    return result
    
def numSents(vOfv):
    return len(vOfv)

def numRecurs(vOfv):
    return sum([1 for v in vOfv if len(v) > 13])

def numYell(vOfv):
    return sum([1 for v in vOfv for w in v if re.search("[A-Z]{3}", w) and enchant.Dict().check(w)])

def numWords(vOfv):
    return sum([len(v) for v in vOfv])

def numGraphs(vOfv):
    return sum([1 for v in vOfv for w in v if re.match(r'([^0-9a-zA-Z])\1\1\1', w)])
    
def numNonAscii(vOfv):
    return sum([1 for v in vOfv for w in v if any(ord(char) > 127 and ord(char) != 8226 for char in w)])

parser = argparse.ArgumentParser()
parser.add_argument("odir", type=argparse_dirtype, help="required json directory")
args = parser.parse_args()
tla = ['abo', 'sub', 'apa', 'cto']
spider = os.path.basename(args.odir)
wdir = os.path.dirname(args.odir)

dt_marker1 = datetime.fromtimestamp(getmtime(os.path.realpath(join(args.odir, 'marker1'))))
utcnow = utc.localize(dt_marker1)
jsons = determine_seven_day_fencepost(utcnow)
craigcr = Json100CorpusReader(args.odir, jsons, dedupe="link")
coords = list(craigcr.coords())
links = list(craigcr.field('link'))
prices = list(craigcr.price())
ids = sorted(list(craigcr.field('id')))
posted = [dateutil.parser.parse(t) for t in list(craigcr.field('posted'))]
bedrooms = []
i2text, i2loc = CorpusDedupe(craigcr, make_dict())

for i, z in enumerate(zip(craigcr.attrs_matching(r'[0-9][bB][rR]'), craigcr.field('title'), craigcr.raw())):
    if z[0] is not None:
        bedrooms.append(int(re.findall(r"[0-9]", z[0])[0]))
    else:
        m = re.search(r'(1|one|2|two|3|three|4|four).{0,9}(b[rd]\b|bed)', z[1] + z[2], re.IGNORECASE)
        if m:
            if re.search(m.group(1), "one", re.IGNORECASE):
                bedrooms.append(1)
            elif re.search(m.group(1), "two", re.IGNORECASE):
                bedrooms.append(2)
            elif re.search(m.group(1), "three", re.IGNORECASE):
                bedrooms.append(3)
            elif re.search(m.group(1), "four", re.IGNORECASE):
                bedrooms.append(4)
            else:
                bedrooms.append(int(m.group(1)))
        else:
            bedrooms.append(0)

firstnames = set()
with open(join(wdir, 'firstnames'), 'r') as f:
    for name in f.readlines():
        name = re.sub('\n', '', name)
        firstnames.add(name)

listedby = []
re_suspect = r"deal|no fee|contact|apartments|apts|for all|llc|to view|([^a-zA-Z0-9]|x)\1\1|rentals|real|estate"
for lister in [re.split(r':\s*', i, 1).pop() if i else None for i in craigcr.attrs_matching(r'[lL]isted')]:
    if lister is not None and not re.search(re_suspect, lister):
        tokens = re.split(r'[^0-9a-zA-Z-]+', lister)
        if len(tokens) >= 2 and len(tokens) < 8:
            for i,z in list(enumerate(tokens))[:-1]:
                if z.lower().split('-')[0] in firstnames:
                    lister = "{} {}".format(tokens[i], tokens[i+1])
                    break
    listedby.append(lister)

oklistedby = set()
for pair in Counter(listedby).iteritems():
    if pair[1] == 1:
	if not re.search(re_suspect, pair[0], re.IGNORECASE):
	    oklistedby.add(pair[0])

odoms = craigcr.attrs_matching(r'[oO]dom')
odoms = [re.split(r':\s*', i, 1).pop() if i else None for i in odoms]

try:
    shutil.rmtree(join(args.odir, 'files'))
except OSError as e:
    if e.errno != errno.ENOENT:
        raise
try:
    os.makedirs(join(args.odir, 'files'))
except OSError as e:
    if e.errno != errno.EEXIST:
        raise

filtered = []
with open(join(args.odir, 'digest'), 'w+') as good, open(join(args.odir, 'reject'), 'w+') as bad:
    for i,z in enumerate(zip(craigcr.docs(), craigcr.raw(newlines_are_periods=True))):
        try:
            listing = '%s %s %s' % ((' '.join([word for sent in z[0] for word in sent][0:50]),                                     links[i],                                     re.sub(r'\s+', ' ', listedby[i]) if listedby[i] else "Actual Person?"))
        except UnicodeEncodeError:
            print  ' '.join([word.encode('utf-8') for sent in z[0] for word in sent])

        # filter in order of increasing time complexity
        if i2text.q_dupe(i):
            bad.write(("dupe %s" % listing).encode('utf-8') + '\n\n')
            continue
        if (utcnow - posted[i]).days >= 7:
            bad.write(("payfor %s" % listing).encode('utf-8') + '\n\n')
            continue
        if listedby[i] is not None and listedby[i] not in oklistedby:
            bad.write(("listedby %s" % listing).encode('utf-8') + '\n\n')
            continue
        if odoms[i] and int(odoms[i]) > 160000:
            bad.write(("miles %s" % listing).encode('utf-8') + '\n\n')
            continue
        if not within(coords[i]):
            bad.write(("toofar %s" % listing).encode('utf-8') + '\n\n')
            continue
        if not listedby[i] and not qPronouns(z[0]):
            bad.write(("pronouns %s" % listing).encode('utf-8') + '\n\n')
            continue
        if re.search(r'leasebreak', z[1]):
            bad.write(("leasebreak %s" % listing).encode('utf-8') + '\n\n')
            continue

        nw=numWords(z[0])
        ns=numSents(z[0])
        ng=numGraphs(z[0])
        wps=float(nw/ns) if ns else 0.0
        nr=numRecurs(z[0])
        np=nPara(z[1])
        spp=float(len(z[0])/np) if np else 0.0
        ny = numYell(z[0])
        yr=float(ny/nw) if nw else 0.0
        nna=numNonAscii(z[0])

        if nna > 3 or spp <= 1.0 or yr > 0.1 or ny > 20 or ng > 3:
            bad.write(listing.encode('utf-8') + '\n\n')
            continue
        good.write(listing.encode('utf-8') + '\n\n')
        filtered.append(i)

        tla_link = re.findall(r"({0})/(?:[^/]+/)*?(\d+).html".format('|'.join(tla)), links[i])[-1]
        with open(join(args.odir, "files", "{}-{}".format(tla_link[0], tla_link[1])), "w") as f:
            f.write(z[1].encode('utf-8'))

red = redis.StrictRedis(host='localhost', port=6379, db=0)
for i, z in enumerate(zip(craigcr.numbers(['price']), craigcr.field('title'))):
    if i in filtered:
        if z[0]['price'] is not None:
            red.hset('item.' + ids[i], 'price', z[0]['price'])
            red.zadd('item.index.price', z[0]['price'], ids[i])
        red.hmset('item.' + ids[i], {'link': links[i], 'title': z[1], 'bedrooms': bedrooms[i], 'coords': coords[i], 'posted': posted[i].isoformat() })
        red.zadd('item.index.bedrooms', bedrooms[i], ids[i])
        if None not in coords[i]:
            red.geoadd('item.geohash.coords', *(tuple(reversed(coords[i])) + (ids[i],)))

