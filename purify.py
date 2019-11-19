# author: Paul Galatic
#
# Program to preprocess Twitter text data and create 'blob files' that contain
# only the text.
#

# STD LIB
import re
import os
import csv
import sys
import time
import string
import pathlib

# EXTERNAL LIB

# PROJECT LIB
from extern import *

# CONSTANTS
TIME_FORMAT = '%H:%M:%S'

def cleanse(target):
    log(f'Purifying {target}...')

    length_before = 0
    length_after = 0
    all_len_diffs = []

    if not os.path.isdir(DATA_DIR):
        os.mkdir(DATA_DIR)

    with open(str(RAW_DIR / target) + '.csv', 'r', encoding='utf-8') as src_file:
        with open(str(DATA_DIR / target) + '.csv', 'w', newline='', encoding='utf-8') as dst_file:
            rdr = csv.reader(src_file)
            wtr = csv.writer(dst_file)

            for row in rdr:
                length_before += len(row[1])

                # Block 1 removes '&amp;' as it is a specific nuisance.
                # Block 2 of this RE removes all usernames.
                # Block 3 removes all punctuation and non-alphanumeric
                #   characters (except apostrophes, @ tags and hashtags).
                # Block 4 removes URLs.
                # text = re.sub('(&amp;)|(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)', ' ', row[1])
                # Currently only using blocks 1, 3, and 4. TODO: Do we want to remove usernames?
                text = re.sub('(&amp;)|([^0-9A-Za-z\'"\.,@# ])|(\w+:\/\/\S+)', ' ', row[1])
                # Get rid of excess spaces.
                text = re.sub('(  +)', ' ', text)

                length_after += len(text)
                all_len_diffs.append((len(row[1]) - len(text)) / len(row[1]))

                row[1] = text
                wtr.writerow(row)

    percent_reduction = round(((length_before - length_after) / length_before) * 100, 3)
    average_reduction = round((sum(all_len_diffs) / len(all_len_diffs) * 100), 3)

    log(f'Stats for {target}:')
    log(f'\ttotal_tweets:\t\t{len(all_len_diffs)}')
    log(f'\tlength_before:\t\t{length_before}')
    log(f'\tlength_after:\t\t{length_after}')
    # Total percentage reduction across the dataset.
    log(f'\tpercent_reduction:\t{percent_reduction}%')
    # Average percentage reduction per tweet.
    log(f'\taverage_reduction:\t{average_reduction}%')
