#
# authors:
#   Paul Galatic
#
# description:
#   Helper functions related to the gathering and storage of data.
#

# STD LIB
import os
import re
import csv
import pdb
import sys
import time
import pprint
import shutil
import pathlib
from datetime import datetime, timedelta

# EXTERNAL LIB
import tweepy

# PROJECT LIB
from extern import log

# CONSTANTS
DST_DIR = pathlib.Path('raw/')
FILTER = ' -filter:retweets'
MAX_TWEETS = 10 ** 9
MAX_CHARS = 10 ** 9

def trending_tweets(api, woeid, num_topics):
    
    # Grabs all trending topics with a known tweet volume.
    topics = [topic for topic in api.trends_place(woeid)[0]['trends'] if topic['tweet_volume'] != None]
    
    # Sort trending topics by their tweet volume. Topics with more tweets are more likely to be
    # interesting, and more data is always helpful.
    # top_topics = sorted(topics, key=lambda topic: topic['tweet_volume'], reverse=True)
    top_topics = topics
    
    # Create the data folder if it doesn't exist.
    if not os.path.isdir(DST_DIR):
        os.mkdir(DST_DIR)
    
    # Process the first N topics.
    for trend in top_topics[:num_topics]:
        
        hashtag = trend['name']
        log(f'Gathering tweets for {hashtag}...')
        
        # Only consider trends with at least one English letter, for now.
        # This introduces bias but makes results more interpretable.
        if re.search('[a-zA-Z]', hashtag):
        
            # Search for tweets matching the hashtag.
            total_length = 0
            total_tweets = 0
            tweet_idx = 0
                        
            # Make a file to store the tweets in.
            fname = str(DST_DIR / (hashtag + '.csv'))
            with open(fname, 'w+', newline='', encoding='utf-8') as topicfile:
            
                # Use a cursor to find tweets and a csv writer to record them.
                # Retweets would lead to data duplication, so those are skipped.
                wtr = csv.writer(topicfile)
                cursor = tweepy.Cursor(
                    api.search, 
                    q=hashtag + FILTER,
                    count=100,
                    lang='en',
                    since=datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d'),
                    tweet_mode='extended'
                )
                
                for tweet in cursor.items():
                    tweet = tweet._json
                        
                    # Record the body of the tweets and the timestamp.
                    text = tweet['full_text']
                    timestamp = tweet['created_at']
                    coords = tweet['coordinates']

                    wtr.writerow([timestamp, text, coords])
                    
                    total_length += len(text)
                    total_tweets += 1
                    
                    if total_length > MAX_CHARS or total_tweets > MAX_TWEETS:
                        log('...Quota met.')
                        break
    
        log(f'stats for {hashtag}')
        log(f'\ttotal_length:\t{total_length}')
        log(f'\ttotal_tweets:\t{total_tweets}')