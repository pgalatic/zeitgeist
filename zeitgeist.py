#
# authors:
#   Paul Galatic
#
# description:
#   App to read trending hashtags and develop summary of what people are talking about, related
#   to a given hashtag.
#

# STD LIB
import os
import sys
import argparse
import traceback

# EXTERNAL LIB
import tweepy

# PROJECT LIB
import gather
from extern import log

# CONSTANTS

def parse_args():
    ap = argparse.ArgumentParser()
    
    ap.add_argument('--num_topics', nargs='?', const=1, default=1,
        help='How many datasets should be analyzed?')
    # Default location of interest is the United States.
    ap.add_argument('--woeid', nargs='?', const=23424977, default=23424977,
        help='Yahoo \"Where On Earth\" ID. Trends will be sourced from this location')
    
    return ap.parse_args()

def main():
    args = parse_args()

    try:
        auth = tweepy.OAuthHandler(os.environ['CONSUMER_KEY'], os.environ['CONSUMER_SECRET'])
        auth.set_access_token(os.environ['ACCESS_TOKEN'], os.environ['ACCESS_TOKEN_SECRET'])
    except KeyError:
        log('One or more keys is missing. See traceback below for details.')
        traceback.print_exc()
        sys.exit(-1)

    api = tweepy.API(auth,
        wait_on_rate_limit=True, 
        wait_on_rate_limit_notify=True)
    
    gather.trending_tweets(api, args.woeid, args.num_topics)

if __name__ == '__main__':
    log('usage: python driver')