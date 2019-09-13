#
# authors:
#   Paul Galatic
#
# description:
#   Helper functions related to general functionality.
#

# STD LIB
import time

# EXTERNAL LIB

# PROJECT LIB

# CONSTANTS
TIME_FORMAT = '%H:%M:%S'

def log(*args):
    '''More informative print debugging'''
    t = time.strftime(TIME_FORMAT, time.localtime())
    s = ' '.join([str(arg) for arg in args])
    print(f'[{t}]: {s}')