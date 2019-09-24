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
import time
import pprint
import shutil
import pathlib
from datetime import datetime, timedelta

# EXTERNAL LIB
import tweepy
import progressbar as pbar

# PROJECT LIB
from extern import log

# CONSTANTS
DATA_DIR = pathlib.Path('data/')

MAX_TWEETS = 10 ** 4
MAX_CHARS = 10 ** 7

class Listener(tweepy.StreamListener):
    
    def __init__(self, csv_writer, timeout):
        self.csv_writer = csv_writer
        self.timeout = timeout
        self.start = time.time()
    
    def on_status(self, status):
        self.csv_writer.writerow([status.timestamp, status.full_text])
        if time.time() - self.start > self.timeout:
            return False
        return True

def trending_tweets(api, woeid, num_topics, stream_length):
    
    # Grabs all trending topics with a known tweet volume.
    topics = [topic for topic in api.trends_place(woeid)[0]['trends'] if topic['tweet_volume'] != None]
    
    # Sort trending topics by their tweet volume. Topics with more tweets are more likely to be
    # interesting, and more data is always helpful.
    top_topics = sorted(topics, key=lambda topic: topic['tweet_volume'], reverse=True)
    
    # Create the data folder if it doesn't exist.
    if not os.path.isdir(DATA_DIR):
        os.mkdir(DATA_DIR)
    
    # Process the first N topics.
    for trend in top_topics[:num_topics]:
        
        hashtag = trend['name']
        log(f'Gathering tweets for {hashtag}...')
        
        # Only consider trends with at least one English letter, for now.
        # This introduces bias but makes results more interpretable.
        if re.search('[a-zA-Z]', hashtag):
        
            # Search for tweets matching the hashtag.
            total_chars = 0
            total_tweets = 0
            tweet_idx = 0
                        
            # Make a file to store the tweets in.
            fname = str(DATA_DIR / (hashtag + '.csv'))
            with open(fname, 'w+', newline='', encoding='utf-8') as topicfile:
            
                # Use a cursor to find tweets and a csv writer to record them.
                # Retweets would lead to data duplication, so those are skipped.
                wtr = csv.writer(topicfile)
                cursor = tweepy.Cursor(
                    api.search, 
                    q=hashtag + '-filter:retweets',
                    count=MAX_TWEETS,
                    lang='en',
                    since=datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d'),
                    tweet_mode='extended',
                    rpp=100
                )
                
                for tweet in cursor.items():
                    tweet = tweet._json
                        
                    # Record the body of the tweets and the timestamp.
                    text = tweet['full_text']
                    timestamp = tweet['created_at']
                
                    wtr.writerow([timestamp, text])
                    
                    total_chars += len(text)
                    total_tweets += 1
                    
                    if total_chars > MAX_CHARS or total_tweets > MAX_TWEETS:
                        log('...That\'s enough for now.')
                        break
                
                if stream_length > 0:
                    listener = Listener(wtr, stream_length)
                    stream = tweepy.Stream(auth=api.auth, listener=listener)
                    stream.filter(track=[hashtag], is_async=True)
                    log(f'Streaming for {stream_length} seconds...')
                    for idx in pbar.progressbar(range(stream_length)):
                        time.sleep(1)
    
        log(f'stats for {hashtag}')
        log(f'\ttotal_chars:\t{total_chars}')
        log(f'\ttotal_tweets:\t{total_tweets}')