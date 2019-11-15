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
import pdb
import time
import pathlib

# EXTERNAL LIB
import numpy as np

# CONSTANTS
DEBUG = True
LOGTIME_FORMAT = '%H:%M:%S'
SAMPLE_SIZE = 2048
SAMPLE = None

RAW_DIR = pathlib.Path('raw/')
DATA_DIR = pathlib.Path('data/')
BRAND_DIR = pathlib.Path('brand/')
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

# Constants for report.py
BORDER = 3
BUFFER = 32
SPACING = BUFFER // 2
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)
ICON = str(BRAND_DIR / 'LOGO.png')
COMMENT = str(BRAND_DIR / 'COMMENT.png')
RETWEET = str(BRAND_DIR / 'RETWEET.png')
LIKE = str(BRAND_DIR / 'LIKE.png')
MAIL = str(BRAND_DIR / 'MAIL.png')
BACKGROUND = str(BRAND_DIR / 'BACKGROUND.png')
FONT_NORM = str(BRAND_DIR / 'HelveticaNeue.ttf')
FONT_BOLD = str(BRAND_DIR / 'helvetica-neue-bold.ttf')
FONT_ROMAN = str(BRAND_DIR / 'helveticaneue-roman.ttf')
TIME_FORMAT = '%a %b %d %H:%M:%S %z %Y'
OUT_FORMAT = '%d %b %Y'

# Constants for gather.py
GATHER_FILTER = ' -filter:retweets'
GATHER_FIELDNAMES = ['index', 'text', 'timestamp', 'fav_count', 'ret_count', 'username', 'at_tag', 'id']
GATHER_MAX_TWEETS = 10 ** 9
GATHER_MAX_CHARS = 10 ** 9

# Constants for cluster.py
NUM_CLUSTERS = 3
DISTANCE_THRESHOLD = 0.975
CORRECT_SPELLING = False
FILTER_STOPWORDS = True # used in cluster.py

# Constants used for summarize.py
REPLACE_DICT = {
    r'w .w' : r'w. w',
    '\.\.'  : '.',
    ' s '   : '\'s ',
    ' t '   : '\'t ',
    ' \. '  : '. ',
    ' Dr '  : ' Dr. ',
    ' Mr '  : ' Mr. ',
    ' Ms '  : ' Ms. ',
    ' Jr '  : ' Jr. ',
    ' Sr '  : ' Sr. '
}
TEST_WIKI_ARTICLE = 'Albert Einstein'
NLP_DOC_LENGTH = 400000
REPEAT_THRESHOLD = 0.30
Q_RANDOM_SEED = 42

# Constants for sentiment.py
K_START = 3
K_END = 15
BEST_K_IDX = 5
DEFAULT_NUM_CLUSTERS = 8
NEUTRAL_CUTOFF = 0.1
MAX_PRINTED_CLUSTERS = 3

def log(*args):
    '''More informative print debugging'''
    t = time.strftime(LOGTIME_FORMAT, time.localtime())
    s = '\t'.join([str(arg) for arg in args])
    print(f'[{t}]: {s}')

def sample(target, size=SAMPLE_SIZE):
    '''
    Returns a sample of rows from a file in DATA_DIR. A sample is only 
    calculated once, and should be re-used between modules.
    '''
    global SAMPLE
    try:
        if SAMPLE == None:
            with open(str(DATA_DIR / target) + '.csv', 'r', newline='', encoding='utf-8') as src:
                rdr = csv.DictReader(src)
                raw = np.array([row for row in rdr])
                SAMPLE = raw[np.random.choice(raw.shape[0], size)]
    except ValueError:
        # Sample already exists.
        pass
    return SAMPLE