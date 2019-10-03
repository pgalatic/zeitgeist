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

# CONSTANTS
TIME_FORMAT = '%H:%M:%S'
RAW_DIR = pathlib.Path('raw/')
DATA_DIR = pathlib.Path('data/')
GATHER_FILTER = ' -filter:retweets'
GATHER_MAX_TWEETS = 10 ** 9
GATHER_MAX_CHARS = 10 ** 9

def log(*args):
    '''More informative print debugging'''
    t = time.strftime(TIME_FORMAT, time.localtime())
    s = ' '.join([str(arg) for arg in args])
    print(f'[{t}]: {s}')