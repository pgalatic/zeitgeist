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
import pprint
import shutil
import pathlib
from datetime import datetime

# EXTERNAL LIB
import tweepy

# PROJECT LIB
from extern import log

# CONSTANTS
DATA_DIR = pathlib.Path('data/')

def trending_tweets(api, num_topics=1, max_tweets=1000, max_chars=10000):
    
    # Grabs all trending topics.
    topics = api.trends_place(1)
    
    # Process the first N topics.
    for trend in topics[0]['trends'][:num_topics]:
        
        hashtag = trend['name']
        
        # Only consider trends with at least one English letter, for now.
        # This introduces bias but makes results more interpretable.
        if re.search('[a-zA-Z]', hashtag):
        
            # Search for tweets matching the hashtag.
            total_chars = 0
            total_tweets = 0
            tweet_idx = 0
                        
            # Make a file to store the tweets in.
            fname = str(DATA_DIR / (hashtag + '.csv'))
            with open(fname, 'w', newline='', encoding='utf-8') as topicfile:
            
                # Use a cursor to find tweets and a csv writer to record them.
                wtr = csv.writer(topicfile)
                cursor = tweepy.Cursor(
                    api.search, 
                    q=hashtag, 
                    count=max_tweets, 
                    lang='en', 
                    since=datetime.today().strftime('%Y-%m-%d'),
                    tweet_mode='extended'
                )
                
                for tweet in cursor.items():
                    tweet = tweet._json

                    # Retweets would lead to data duplication, so those are skipped.
                    if not tweet['retweeted'] and 'RT @' not in tweet['full_text']:
                        
                        # Record the body of the tweets and the timestamp.
                        text = tweet['full_text']
                        timestamp = tweet['created_at']
                    
                        wtr.writerow([timestamp, text])
                        
                        total_chars += len(text)
                        total_tweets += 1
                        
                        if total_chars > max_chars or total_tweets > max_tweets: break
    
        log(f'stats for {hashtag}')
        log(f'\ttotal_chars:\t{total_chars}')
        log(f'\ttotal_tweets:\t{total_tweets}')