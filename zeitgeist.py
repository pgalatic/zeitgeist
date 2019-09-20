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
import traceback

# EXTERNAL LIB
import tweepy

# PROJECT LIB
import gather
from extern import log

# CONSTANTS

def main():
    try:
        auth = tweepy.OAuthHandler(os.environ['CONSUMER_KEY'], os.environ['CONSUMER_SECRET'])
        auth.set_access_token(os.environ['ACCESS_TOKEN'], os.environ['ACCESS_TOKEN_SECRET'])
    except KeyError:
        log('One or more keys is missing. See traceback below for details.')
        traceback.print_exc()
        sys.exit(-1)

    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    
    gather.trending_tweets(api)

if __name__ == '__main__':
    log('usage: python driver')