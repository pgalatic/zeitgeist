#
# authors:
#   Paul Galatic
#
# description:
#   Helper functions related to general functionality.
#

# STD LIB
import os
import csv
import time
import pathlib

# EXTERNAL LIB
import numpy as np

# CONSTANTS
TIME_FORMAT = '%H:%M:%S'
SAMPLE_SIZE = 2048
SEED = None

RAW_DIR = pathlib.Path('raw/')
DATA_DIR = pathlib.Path('data/')
CACHE_DIR = pathlib.Path('cache/')
REPORT_DIR = pathlib.Path('report/')

if not os.path.exists(RAW_DIR):
    os.mkdir(RAW_DIR)
if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)
if not os.path.exists(CACHE_DIR):
    os.mkdir(CACHE_DIR)
if not os.path.exists(REPORT_DIR):
    os.mkdir(REPORT_DIR)

# Constants for gather.py
GATHER_FILTER = ' -filter:retweets'
GATHER_MAX_TWEETS = 10 ** 9
GATHER_MAX_CHARS = 10 ** 9

# Constants for cluster.py
NUM_CLUSTERS = 3
DISTANCE_THRESHOLD = 0.975
CORRECT_SPELLING = False
FILTER_STOPWORDS = True # used in cluster.py

# Constants used for summarize.py
TEST_WIKI_ARTICLE = 'Albert Einstein'
NLP_DOC_LENGTH = 400000
REPEAT_THRESHOLD = 0.30

# Constants for sentiment.py
K_START = 3
K_END = 15
BEST_K_IDX = 5
NEUTRAL_CUTOFF = 0.1
MAX_PRINTED_CLUSTSERS = 5

def log(*args):
    '''More informative print debugging'''
    t = time.strftime(TIME_FORMAT, time.localtime())
    s = ' '.join([str(arg) for arg in args])
    print(f'[{t}]: {s}')

def sample(target):
    if SEED: np.random.seed(SEED)
    with open(str(DATA_DIR / target) + '.csv.', 'r', newline='', encoding='utf-8') as src:
        rdr = csv.reader(src)
        raw_data = [row[1] for row in rdr]
        return np.random.choice(raw_data, SAMPLE_SIZE)