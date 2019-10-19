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
import sentiment
from extern import *

def arg_parser():
    ap = argparse.ArgumentParser()
    
    ### Arguments for specifying pipeline (what code blocks should be executed)
    # Run full program
    ap.add_argument('--full', action='store_true',
        help='Run full analysis path on current Twitter data [False]')
    # Run full program on [file] (does not collect new data)
    ap.add_argument('--process', nargs='?', const=None, default=None,
        help='Use if data has already been collected, e.g. \'--process=#WednesdayWisdom\'. [None]')
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
    # Run sentiment analysis on [file]
    ap.add_argument('--sentiment', nargs='?', const=None, default=None,
        help='Performs sentiment analysis on a file, e.g. \'--sentiment=#WednesdayWisdom\'. [None]')
        
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

def gather_data(woeid, num_topics):
    # We have to validate our Twitter API before we run Gather.
    try:
        log('Validating Twitter API...')
        auth = tweepy.OAuthHandler(os.environ['CONSUMER_KEY'], os.environ['CONSUMER_SECRET'])
        auth.set_access_token(os.environ['ACCESS_TOKEN'], os.environ['ACCESS_TOKEN_SECRET'])
    except KeyError:
        log('One or more keys is missing. See traceback below for details.')
        traceback.print_exc()
        sys.exit(-1)

    log('Gathering data (crtl+C to stop early)...')
    # Tweepy SHOULD notify us if we're getting rate limited. Often it just
    # quits, though. If it doesn't quit, then the user can progress to the 
    # next step via crtl+C.
    api = tweepy.API(auth,
        wait_on_rate_limit=True,
        wait_on_rate_limit_notify=True)
    # Trending tweets are stored in a CSV file in the /raw/ directory.
    gather.trending_tweets(api, woeid, num_topics) 

def process(target=None):
    '''
    Gathering data takes a long time, so if we want to process an existing 
    dataset, we can use this function as shorthand.
    '''
    if not target: target = most_recent_file(RAW_DIR)
    partial(**{
        'purify': target,
        'cluster': target,
        'summarize': target,
        'sentiment': target
    })

def partial(**kwargs):
    if kwargs.get('gather'):
        # If we want to gather data (or we're running everything), call the 
        # Twitter API and gather as much as we can.
        gather_data(kwargs.get('woeid'), kwargs.get('num_topics'))
    if kwargs.get('purify'):
        # If we want to clean data (or we're running everything), grab a target
        # and feed it through the data cleaning algorithm. If a target isn't 
        # specified, the most recent file is used.
        purify.cleanse(kwargs['purify'])
    if kwargs.get('cluster'):
        # Same as above, but for clustering.
        if not os.path.exists(str(DATA_DIR / kwargs['cluster']) + '.csv'):
            purify.cleanse(kwargs['cluster'])
        cluster.agglomerate(kwargs['cluster'])
    if kwargs.get('summarize'):
        # Same as above, but for text summarization. FIXME: This function seems
        # to perform so poorly that it can temporarily freeze computers, and is 
        # deactivated pending investigation.
        if not os.path.exists(str(DATA_DIR / kwargs['summarize']) + '.csv'):
            purify.cleanse(kwargs['summarize'])
        # summary = summarize.summarize_tweets(kwargs['summarize'])
        # log(summary)
    if kwargs.get('sentiment'):
        # Same as above, but for sentiment analysis
        tweets = sentiment.reduce_to_indv_tweet_text(kwargs['sentiment'])
        tweets_df = sentiment.get_sentiment_data_frame(tweets)
        sentiment.numerical_sentiment_analysis(tweets_df)
        sentiment.sentiment_clustering(tweets_df)

def main():
    parser = arg_parser()
    args = parser.parse_args()

    # If we want to run everything, then run everything.
    if args.full:
        gather_data(args.woeid, args.num_topics)
        process(most_recent_file(RAW_DIR))
    # If we only want to process a specific target, then generate a report 
    # without downloading any new data.
    elif args.process:
        if args.process == 'last':
            process()
        else:
            process(target=args.process)
    # If we're doing things a-la-carte, then pass the arguments to partial().
    elif args.gather or args.purify or args.cluster or args.summarize or args.sentiment:
        partial(**vars(args))
    # Otherwise, print a usage statement.
    else:
        parser.print_help(sys.stdout)

if __name__ == '__main__':
    log('usage: python driver')
