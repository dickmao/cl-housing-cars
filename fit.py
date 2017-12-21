from __future__ import division, print_function
import logging

from time import time
import os, errno, operator, re, sys, subprocess, signal, redis
import itertools, shutil, requests, boto3, pickle

from corenlp import CoreNLPClient, WordTokenizer, SentTokenizer
import numpy as np
import enchant
import matplotlib.pyplot as plt

from gensim import parsing, matutils, interfaces, corpora, models, similarities, summarization
from gensim.utils import lemmatize
from gensim.corpora.mmcorpus import MmCorpus
from gensim.matutils import corpus2csc
from gensim.similarities.docsim import SparseMatrixSimilarity

from collections import Callable
from nltk import collocations, association, text, tree
from nltk import bigrams,ConditionalFreqDist,FreqDist,pos_tag,pos_tag_sents
from nltk.grammar import DependencyGrammar
from nltk.parse import (
    DependencyGraph, ProjectiveDependencyParser, NonprojectiveDependencyParser)

from nltk.corpus import dependency_treebank
from nltk.corpus import treebank_raw
from nltk.corpus import treebank
from nltk.corpus.util import LazyCorpusLoader

import re, json, dateutil.parser, argparse
from os.path import getmtime, join, realpath

from pytz import utc
from datetime import datetime
from dateutil.tz import tzlocal
from bisect import bisect_left

from reader import Json100CorpusReader

import sklearn.externals.joblib
from sklearn.preprocessing import FunctionTransformer
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.feature_selection import SelectFromModel
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.linear_model import RidgeClassifier
from sklearn.pipeline import Pipeline, FeatureUnion, make_pipeline
from sklearn.svm import LinearSVC, SVC
from sklearn.multiclass import OneVsRestClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.linear_model import Perceptron
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn.naive_bayes import BernoulliNB, ComplementNB, MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neighbors import NearestCentroid
from sklearn.ensemble import RandomForestClassifier
from sklearn.utils.extmath import density
from sklearn import metrics
from sklearn.model_selection import GridSearchCV, StratifiedKFold, ParameterGrid

# Display progress logs on stdout
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')


def argparse_dirtype(astring):
    if not os.path.isdir(astring):
        raise argparse.ArgumentError
    return astring

def datetime_parser(json_dict):
    for k,v in json_dict.iteritems():
        try:
            json_dict[k] = dateutil.parser.parse(v)
        except (ValueError, AttributeError):
            pass
    return json_dict

def get_datetime(filename):
    return dateutil.parser.parse(filename.split(".")[1][::-1].replace("-", ":", 2)[::-1]).replace(tzinfo=utc)
    
class CallableAnnotate(Callable):
    def __init__(self, client):
        self._client = client

    def __call__(self, doc):
        ann = self._client.annotate(doc, annotators="ner".split())
        return itertools.chain.from_iterable([[t.lemma for t in s.token if t.pos != "CD"] for s in ann.sentence])

def get_text_length(docs):
    return np.array([len(doc) for doc in docs]).reshape(-1, 1)

class CallableCountPronouns(Callable):
    def __init__(self, client):
        self._client = client

    def __call__(self, docs):
        result = []
        for doc in docs:
            ann = self._client.annotate(doc, annotators="ner".split())
            result.append(sum(itertools.chain.from_iterable([[1 for t in s.token if (t.pos == "PRP" or t.pos == "PRP$")] for s in ann.sentence])))
        return np.asarray(result).reshape(-1, 1)

def main():
    argparser = argparse.ArgumentParser()

    # argparser.add_argument('--folders', nargs='*', type=str, help='s3 paths')
    # argparser.add_argument('--files', nargs='*', type=str, help='s3 paths')
    # argparser.add_argument('exec', type=str, help='s3 path')
    argparser.add_argument('--working-dir', type=argparse_dirtype, default='.')
    argparser.add_argument('--corenlp-uri', type=str, default='http://localhost:9005')
    args = argparser.parse_args()
    os.chdir(args.working_dir)

    s3 = boto3.resource('s3')
    bucket = s3.Bucket("303634175659.newyork")
    with open('/var/tmp/marker1.pkl', 'wb') as marker1:
        bucket.download_fileobj('marker1.pkl', marker1)
    with open('/var/tmp/marker1.pkl', 'rb') as marker1:
        dt_marker1 = pickle.load(marker1)

    (Markers, jsons) = ([], [])
    for obj in bucket.objects.all():
        if re.match(r'Marker', obj.key):
            dt = get_datetime(obj.key)
            if (dt_marker1 - dt).days < 30:
                Markers.append(obj.key)
                if not os.path.exists(join(".", obj.key)):
                    bucket.download_file(obj.key, join(".", obj.key))
    for m in sorted(Markers, reverse=True):
        within = False
        with open(m, 'r') as fp:
            url2dt = json.load(fp, object_hook=datetime_parser)
            for url,dt0 in url2dt.iteritems():
                if (dt_marker1 - dt0).days < 9:
                    within = True
                    break
        if within:
            body = "dmoz.{}".format(m.split(".", 1)[1])
            jsons.append(join(".", body))
            if not os.path.exists(join(".", body)):
                bucket.download_file(body, join(".", body))
        else:
            break

    with CoreNLPClient(start_cmd="gradle -p {} server".format("../CoreNLP"), endpoint=args.corenlp_uri, timeout=15000) as client:
        cr = Json100CorpusReader(".", jsons, dedupe="id", word_tokenizer=WordTokenizer(client), sent_tokenizer=SentTokenizer(client))
        crabo = Json100CorpusReader(".", jsons, dedupe="id", link_select='abo', word_tokenizer=WordTokenizer(client), sent_tokenizer=SentTokenizer(client))
        crsub = Json100CorpusReader(".", jsons, dedupe="id", link_select='sub', word_tokenizer=WordTokenizer(client), sent_tokenizer=SentTokenizer(client))
        crjoin = Json100CorpusReader(".", ["joinery.json"], dedupe="id", word_tokenizer=WordTokenizer(client), sent_tokenizer=SentTokenizer(client))
        crlp = Json100CorpusReader(".", ["listingsproject.json"], dedupe="id", word_tokenizer=WordTokenizer(client), sent_tokenizer=SentTokenizer(client))

        crtrain_desc = list(itertools.chain(crabo.field('desc'), crlp.field('desc')))
        crtrain_labels = [-1] * len(crabo) + [1] * len(crlp)
        crtest_desc = list(itertools.chain(crsub.field('desc'), crjoin.field('desc')))
        crtest_labels = [-1] * len(crsub) + [1] * len(crjoin)

        features = FeatureUnion([
                ('text', Pipeline([
                    ('vectorizer', CountVectorizer(max_df=0.5, min_df=2, analyzer=CallableAnnotate(client))),
                    ('tfidf', TfidfTransformer()),
                ])),
                ('length', Pipeline([
                    ('count', FunctionTransformer(get_text_length, validate=False)),
                ])),
                ('pronouns', Pipeline([
                    ('count', FunctionTransformer(CallableCountPronouns(client), validate=False)),
                ])),
        ])

        # pickling with count_pronouns will defeat:
        # memory=sklearn.externals.joblib.Memory(cachedir="/var/tmp", verbose=0)
        # svc = make_pipeline(features, SVC(C=10,kernel='linear'), memory=None)
        svc = make_pipeline(features, SVC(C=10,kernel='linear'), memory=sklearn.externals.joblib.Memory(cachedir="/var/tmp", verbose=0))
        svc.fit(crtrain_desc, crtrain_labels)
        y_pred = svc.predict(crtest_desc)
        print(metrics.accuracy_score(crtest_labels, y_pred))
        print(metrics.confusion_matrix(crtest_labels, y_pred))
        sklearn.externals.joblib.dump(svc.named_steps['svc'], 'fit.pkl')
        

if __name__ == '__main__':
    main()
