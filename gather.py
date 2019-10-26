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
from datetime import datetime, timedelta

# EXTERNAL LIB
import tweepy

# PROJECT LIB
from extern import *

# CONSTANTS


def already_downloaded():
    '''
    Returns the names of files in RAW_DIR, WITHOUT their extensions. Example:
    
    raw/
        #ImpeachTrump.csv
        #WednesdayWisdom.csv
    
    returns: {#ImpeachTrump, #WednesdayWisdom}
    '''
    topics = set()
    for fname in os.listdir(RAW_DIR):
        topics.add(os.path.splitext(fname)[0])
    return topics

def trending_tweets(api, woeid, num_topics):
    
    # Create the data folder if it doesn't exist.
    if not os.path.isdir(RAW_DIR):
        os.mkdir(RAW_DIR)
    
    # Grabs all trending topics with a known tweet volume.
    topics = []
    redundant = already_downloaded()
    for trend in api.trends_place(woeid)[0]['trends']:
        # Ignore any topics that are empty or those that we've already downloaded.
        if trend['tweet_volume'] != None and trend['name'] not in redundant:
            topics.append(trend)
    
    # Process the first N topics.
    for trend in topics[:num_topics]:
        
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
            fname = str(RAW_DIR / (hashtag + '.csv'))
            with open(fname, 'w+', newline='', encoding='utf-8') as topicfile:
            
                # Use a cursor to find tweets and a csv writer to record them.
                # Retweets would lead to data duplication, so those are skipped.
                wtr = csv.writer(topicfile)
                cursor = tweepy.Cursor(
                    api.search, 
                    q=hashtag + GATHER_FILTER,
                    count=100,
                    lang='en',
                    since=datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d'),
                    tweet_mode='extended'
                )
                
                try:
                    for tweet in cursor.items():
                        tweet = tweet._json
                            
                        # Record the body of the tweets and the timestamp.
                        text = tweet['full_text']
                        timestamp = tweet['created_at']
                        coords = tweet['coordinates']

                        wtr.writerow([timestamp, text, coords])
                        
                        total_length += len(text)
                        total_tweets += 1
                        
                        if total_length > GATHER_MAX_CHARS or total_tweets > GATHER_MAX_TWEETS:
                            log('...Quota met.')
                            break
                except KeyboardInterrupt:
                    pass
    
        log(f'stats for {hashtag}')
        log(f'\ttotal_length:\t{total_length}')
        log(f'\ttotal_tweets:\t{total_tweets}')