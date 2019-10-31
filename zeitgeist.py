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
import textwrap
import argparse
import linecache
import traceback

# EXTERNAL LIB
import tweepy
from PIL import Image, ImageDraw, ImageFont

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
    # Use random seed (or not).
    ap.add_argument('--seed', type=int, nargs='?', const=None, default=None,
        help='Seed for initializing random number generator.')
    # Mock report for the purpose of experimental control.
    ap.add_argument('--mock', action='store_true',
        help='Mock report, choosing random tweets instead of real ones.')
    # Add a label to a report for the purpose of experimental control.
    ap.add_argument('--label', type=str, nargs='?', const=None, default=None,
        help='Adds input as label to top right of report.')
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

def deref(tweets, target):
    '''
    Given a list of tweets from DATA_DIR, replaces their text with the 
    corresponding text from the same tweet in RAW_DIR.
    '''
    tweets = sorted(tweets, key=lambda x: int(x['index']))
    log(tweets)
    with open(str(RAW_DIR / target) + '.csv', 'r', newline='', encoding='utf-8') as raw:
        rdr = csv.DictReader(raw)
        rows = [row for row in rdr]
        
        for idx in range(len(tweets)):
            tweets[idx]['text'] = rows[idx]['text']
    log(tweets)

def report(target, summary, cluster_reps, sent_reps, seed=None, label=None):
    '''
    Takes data generated by the rest of the program and generates a report.
    '''
    # Some sanity checks to make sure we have the right data.
    assert(type(summary) == str)
    assert(len(cluster_reps) == 3)
    assert(len(sent_reps) == 6)
    
    img = Image.open(BACKGROUND)
    smlfnt = ImageFont.truetype(FONT_BOLD, 32)
    fnt = ImageFont.truetype(FONT_BOLD, 48)
    bigfnt = ImageFont.truetype(FONT_BOLD, 128)
    
    width, height = img.size
    label_loc =     (width * 0.80, height * 0.10)
    seed_loc =      (width * 0.10, height * 0.10)
    title_loc =     (width * 0.30, height * 0.10)
    summary_loc =   (width * 0.05, height * 0.20)
    cluster_0_loc = (width * 0.05, height * 0.45)
    cluster_1_loc = (width * 0.35, height * 0.45)
    cluster_2_loc = (width * 0.65, height * 0.45)
    sent_0_loc =    (width * 0.05, height * 0.65)
    sent_1_loc =    (width * 0.35, height * 0.65)
    sent_2_loc =    (width * 0.65, height * 0.65)
    sent_3_loc =    (width * 0.05, height * 0.85)
    sent_4_loc =    (width * 0.35, height * 0.85)
    sent_5_loc =    (width * 0.65, height * 0.85)
    
    summary = '\n'.join(textwrap.wrap(summary, width=80))
    cluster_text = ['\n'.join(textwrap.wrap(rep[2]['text'], width=32)) for rep in cluster_reps]
    sent_text = ['\n'.join(textwrap.wrap(rep, width=32)) for rep in sent_reps]
    
    draw = ImageDraw.Draw(img)
    if label: draw.text(label_loc, f'label={label}', fill=(0, 0, 0), font=smlfnt)
    if seed: draw.text(seed_loc, f'seed={seed}', fill=(0, 0, 0), font=smlfnt)
    draw.text(title_loc, '\n' + target, fill=(0, 0, 0), font=bigfnt, align='center')
    draw.text(summary_loc, summary, fill=(0, 0, 0), font=fnt)
    draw.text(cluster_0_loc, cluster_text[0], fill=(0, 0, 0), font=fnt, align='center')
    draw.text(cluster_1_loc, cluster_text[1], fill=(0, 0, 0), font=fnt, align='center')
    draw.text(cluster_2_loc, cluster_text[2], fill=(0, 0, 0), font=fnt, align='center')
    draw.text(sent_0_loc, sent_text[0], fill=(0, 0, 0), font=fnt, align='center')
    draw.text(sent_1_loc, sent_text[1], fill=(0, 0, 0), font=fnt, align='center')
    draw.text(sent_2_loc, sent_text[2], fill=(0, 0, 0), font=fnt, align='center')
    draw.text(sent_3_loc, sent_text[3], fill=(0, 0, 0), font=fnt, align='center')
    draw.text(sent_4_loc, sent_text[4], fill=(0, 0, 0), font=fnt, align='center')
    draw.text(sent_5_loc, sent_text[5], fill=(0, 0, 0), font=fnt, align='center')
    
    img.save(str(REPORT_DIR / target) + '.png')

def process(target=None, mock=None, seed=None, label=None):
    '''
    Gathering data takes a long time, so if we want to process an existing 
    dataset, we can use this function as shorthand.
    '''
    if not target: target = most_recent_file(RAW_DIR)
    partial(**{
        'purify': target,
        'cluster': target,
        'summarize': target,
        'sentiment': target,
        'report': target,
        'mock': mock,
        'seed': seed,
        'label': label,
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
    if kwargs.get('summarize'):
        # Same as above, but for text summarization.
        if not os.path.exists(str(DATA_DIR / kwargs['summarize']) + '.csv'):
            purify.cleanse(kwargs['summarize'])
        try:
            summary = summarize.summarize_tweets(kwargs['summarize'], kwargs['mock'])
            # TODO: ADD SUMMARY TO REPORT HERE
            log(summary)
        except MemoryError:
            log('WARN: Not enough memory to perform summarization!')
    if kwargs.get('cluster'):
        # Find representative tweets using agglomerative clustering. 
        if not os.path.exists(str(DATA_DIR / kwargs['cluster']) + '.csv'):
            purify.cleanse(kwargs['cluster'])
        cluster_reps = cluster.find_cluster_reps(kwargs['cluster'], kwargs['mock'])
        deref([rep[2] for rep in cluster_reps], kwargs['cluster'])
        for idx in range(len(cluster_reps)):
            log(f'Cluster size:\t{cluster_reps[idx][0]}')
            log(f'Confidence:\t{round(cluster_reps[idx][1], 2)}')
            text = cluster_reps[idx][2]['text']
            log(f'Tweet:\t{text}')
    if kwargs.get('sentiment'):
        # Same as above, but for sentiment analysis
        tweets_df = sentiment.get_sentiment_data_frame(kwargs['sentiment'])
        # TODO: TBENDLIN -- PACKAGE YOUR RETURN DATA SO THAT IT CAN BE ADDED
        #     TO THE REPORT HERE, IN ZEITGEIST.PY. YOU NEED TO RETURN THE FULL
        #     ROW OF THE TWEET SO THAT IT CAN BE DEREFERENCED.
        sentiment.numerical_sentiment_analysis(tweets_df, kwargs['mock'])
        sentiment.sentiment_clustering(tweets_df, kwargs['mock'])
        # TODO: ADD SENTIMENT TO REPORT HERE
        raw_sentiment_reps = [f'TODO SENTIMENT {idx}' for idx in range(6)]
     
    if kwargs.get('report'):
        # Use the target for sentiment here (it is the same as the targets for 
        # the other submodules when args.full or args.process is run).
        report(kwargs.get('report'), summary, 
            cluster_reps, 
            raw_sentiment_reps,
            kwargs.get('seed'),
            kwargs.get('label'),
        )

def main():
    parser = arg_parser()
    args = parser.parse_args()
    
    # Set the random number generator seed if one has been provided.
    if args.seed: np.random.seed(args.seed)
    # We should NEVER mock a report without using a random seed.
    if args.mock and not (args.seed and args.label):
        raise Exception('Never mock a report without using a random seed and a label!')

    # If we want to run everything, then run everything.
    if args.full:
        gather_data(args.woeid, args.num_topics)
        process(most_recent_file(RAW_DIR), args.seed, args.label)
    # If we only want to process a specific target, then generate a report 
    # without downloading any new data.
    elif args.process:
        process(target=args.process, mock=args.mock, seed=args.seed, label=args.label)
    # If we're doing things a-la-carte, then pass the arguments to partial().
    elif args.gather or args.purify or args.cluster or args.summarize or args.sentiment:
        partial(**vars(args))
    # Otherwise, print a usage statement.
    else:
        parser.print_help(sys.stdout)

if __name__ == '__main__':
    log('usage: python driver')
