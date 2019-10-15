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
import glob
import argparse
import traceback

# EXTERNAL LIB
import tweepy

# PROJECT LIB
import gather
import purify
import cluster
import summarize
from extern import *

def arg_parser():
    ap = argparse.ArgumentParser()
    
    ### Arguments for specifying pipeline (what code blocks should be executed)
    # Run full program
    ap.add_argument('--full', action='store_true',
        help='Run full analysis path on current Twitter data [False]')
    # Run data collection
    ap.add_argument('--gather', action='store_true',
        help='Gather new data from Twitter [False]')
    # Run data purification on [flie]
    ap.add_argument('--purify', nargs='?', const=None, default=None,
        help='Specify a target for data cleaning, e.g. \'--purify=#WednesdayWisdom\'. [None]')
    # Run data clustering on [file]
    ap.add_argument('--cluster', nargs='?', const=None, default=None,
        help='Specify a target for tweet clustering, e.g. \'--cluster=#WednesdayWisdom\'. [None]')
    # Run data summarization on [file]
    ap.add_argument('--summarize', nargs='?', const=None, default=None,
        help='Summarizes a file, e.g. \'--summarize=#WednesdayWisdom\'. [None]')
        
    ### Arguments modifying behavior
    # Number of topics to analyze.
    ap.add_argument('--num_topics', nargs='?', type=int, const=1, default=1,
        help='Can only be used when --gather==True. How many datasets should be analyzed? [1]')
    # Default location of interest is the United States.
    ap.add_argument('--woeid', nargs='?', type=int, const=23424977, default=23424977,
        help='Can only be used wehn --gather==True. Yahoo \"Where On Earth\" ID. Trends will be sourced from this location. [23424977 (United States)]')

    return ap

def most_recent_file(dir):
    '''Gets the most recent file from a directory.'''
    recent_files = glob.glob(str(dir / '*.csv'))
    if len(recent_files) < 1:
        log(f'WARN: There are no recent files in the {RAW_DIR} ' +\
            'directory. Are you sure you have any data?')
        sys.exit(1)
    most_recent_file = max(recent_files, key=os.path.getctime)
    
    topic_name = os.path.splitext(os.path.basename(most_recent_file))[0]
    return topic_name

def main():
    parser = arg_parser()
    args = parser.parse_args()

    try:
        auth = tweepy.OAuthHandler(os.environ['CONSUMER_KEY'], os.environ['CONSUMER_SECRET'])
        auth.set_access_token(os.environ['ACCESS_TOKEN'], os.environ['ACCESS_TOKEN_SECRET'])
    except KeyError:
        log('One or more keys is missing. See traceback below for details.')
        traceback.print_exc()
        sys.exit(-1)

    if args.gather:
        # If we want to gather data (or we're running everything), call the 
        # Twitter API and gather as much as we can.
        log('Gathering data (crtl+C to stop early)...')
        # Tweepy SHOULD notify us if we're getting rate limited. Often it just
        # quits, though. If it doesn't quit, then the user can progress to the 
        # next step via crtl+C.
        api = tweepy.API(auth,
            wait_on_rate_limit=True,
            wait_on_rate_limit_notify=True)
        # Trending tweets are stored in a CSV file in the /raw/ directory.
        gather.trending_tweets(
            api,
            woeid=args.woeid,
            num_topics=args.num_topics)
    
    # This may have changed since the last gather.
    most_recent_topic = most_recent_file(RAW_DIR)
    if not os.path.exists(REPORT_DIR):
        os.mkdir(REPORT_DIR)
    
    if args.purify or args.full:
        # If we want to clean data (or we're running everything), grab a target
        # and feed it through the data cleaning algorithm. If a target isn't 
        # specified, the most recent file is used.
        purify_target = args.purify if args.purify else most_recent_topic
        purify.cleanse(purify_target)
    if args.cluster or args.full:
        # Same as above, but for clustering.
        cluster_target = args.cluster if args.cluster else most_recent_topic
        if not os.path.exists(str(DATA_DIR / cluster_target) + '.csv'):
            purify.cleanse(cluster_target)
        cluster.agglomerate(cluster_target)
    if args.summarize or args.full:
        # Same as above, but for text summarization.
        summarize_target = args.summarize if args.summarize else most_recent_topic
        if not os.path.exists(str(DATA_DIR / summarize_target) + '.csv'):
            purify.cleanse(summarize_target)
        summary = summarize.summarize_tweets(summarize_target)
        log(summary)
    
    if not (args.full or args.gather or args.purify or args.cluster or args.summarize):
        parser.print_help(sys.stdout)

if __name__ == '__main__':
    log('usage: python driver')
