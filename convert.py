# author: Paul Galatic
#
# Program to assist in data conversion.

# STD LIB
import csv
import sys
import argparse

# LOCAL LIB
from extern import *

# CONSTANTS
TIME_FORMAT = '%H:%M:%S'

def parse_args():
    '''Parses arguments'''
    ap = argparse.ArgumentParser()
    
    ap.add_argument('fname', type=str,
        help='The file to convert into the new format. THE FULL PATH IS REQUIRED.')
    
    return ap.parse_args()
    
def main():
    '''Driver program'''
    args = parse_args()
    log('Starting...')

    with open(args.fname, 'r', newline='', encoding='utf-8') as readin:
        rdr = csv.reader(readin)
        newrows = []
        
        counter = 0
        for row in rdr:
            if row[-1] == 'id':
                # The header is here, so we've already converted this file.
                log('This file has already been converted.')
                sys.exit(1)
            newrow = {
                'index': counter, 
                'text': row[1], 
                'timestamp': row[0], 
                'fav_count': None, 
                'ret_count': None, 
                'username': None, 
                'at_tag': None,
                'id': None
            }
            newrows.append(newrow)
            counter += 1
    
    with open(args.fname, 'w', newline='', encoding='utf-8') as writeout:
        wtr = csv.DictWriter(writeout, fieldnames=GATHER_FIELDNAMES)
        wtr.writeheader()
        for row in newrows:
            wtr.writerow(row)

    log('...finished.')
    return 0

if __name__ == '__main__':
    main()