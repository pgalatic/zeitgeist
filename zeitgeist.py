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
import purify
from extern import log

# CONSTANTS

def parse_args():
    ap = argparse.ArgumentParser()
    
    # Number of topics to analyze.
    ap.add_argument('--num_topics', nargs='?', type=int, const=1, default=1,
        help='How many datasets should be analyzed? [1]')
    # Default location of interest is the United States.
    ap.add_argument('--woeid', nargs='?', type=int, const=23424977, default=23424977,
        help='Yahoo \"Where On Earth\" ID. Trends will be sourced from this location. [23424977 (United States)]')
    # Should we analyze a specific file? If there is no target, then we gather data.
    ap.add_argument('--target', nargs='?', const=None, default=None,
        help='Specify a target for analysis, such as \'#WednesdayWisdom\'. If there is no target, perform data collection. [None]')
    
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

    log(args.target)
    if args.target == None:
        log('Gathering data...')
    
        api = tweepy.API(auth,
            wait_on_rate_limit=True, 
            wait_on_rate_limit_notify=True)
        
        gather.trending_tweets(
            api,
            woeid=args.woeid,
            num_topics=args.num_topics)
    else:
        log(f'Purifying {args.target}...')
        purify.cleanse(args.target)

if __name__ == '__main__':
    log('usage: python driver')