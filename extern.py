#
# authors:
#   Paul Galatic
#
# description:
#   Helper functions related to general functionality.
#

# STD LIB
import time
import pathlib

# EXTERNAL LIB
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords

# CONSTANTS
TIME_FORMAT = '%H:%M:%S'
RAW_DIR = pathlib.Path('raw/')
DATA_DIR = pathlib.Path('data/')
CACHE_DIR = pathlib.Path('cache/')
REPORT_DIR = pathlib.Path('report/')

GATHER_FILTER = ' -filter:retweets'
GATHER_MAX_TWEETS = 10 ** 9
GATHER_MAX_CHARS = 10 ** 9
STOPWORDS = set(stopwords.words('english'))

NUM_CLUSTERS = 3
CLUSTERING_SAMPLES = 1000
CORRECT_SPELLING = False
FILTER_STOPWORDS = True # used in cluster.py

def log(*args):
    '''More informative print debugging'''
    t = time.strftime(TIME_FORMAT, time.localtime())
    s = ' '.join([str(arg) for arg in args])
    print(f'[{t}]: {s}')