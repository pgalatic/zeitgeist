# Main Idea:
#	- Text preprocessing (removing stopwards, removing punctuation, etc.)
# 	- Frequency table of words/Word Frequency distribution - how many times each word appears in the document
#	- Score each sentence depending on the words it contains and the frequency table
# 	- build summary by joining ever sentence above a certain score limit
#       NOTE: Might need to run 'python3 -m spacy download en' to download english spacy package

import re
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
import wikipedia
import random as r
from heapq import nlargest
from collections import Counter
from string import punctuation
from extern import *
r.seed(Q_RANDOM_SEED)

# Function to test the functionality of text_summarization.py
def _test():
    wikipedia.set_lang('en')
    document_1 = str(wikipedia.page(TEST_WIKI_ARTICLE).content)

    final_summary = core_summary_function(document_1)
    print(final_summary)

def _is_repeat_sentence(s):
    if type(s) != str:
        s = s.text
    s = s.replace('\n', ' ')
    s_list = s.split(' ')
    counts = Counter(s_list)
    num_words = len(s_list)
    for (w, c) in counts.items():
        if c/num_words > REPEAT_THRESHOLD:
            return True
    return False

# encapsulates logic that is repeated for num_likes and num_retweets
def _get_top_tweets_helper(top_arr, num_for_metric, metric):
    top_n_arr = []
    for i, t in enumerate(top_arr):
        if int(t[metric] if t[metric] else 0) > 0:
            top_n_arr.append(t)
        else:
            zero_idx = i
            break
    zero_occ_for_metric = top_arr[zero_idx:]
    r.shuffle(zero_occ_for_metric)
    num_randomly_sampled_zero_metric_tweets = num_for_metric - len(top_n_arr)
    top_n_arr.extend(zero_occ_for_metric[:num_randomly_sampled_zero_metric_tweets])
    return top_n_arr

def _remove_duplicates(tweets):
    texts = set()
    results = list()
    for tweet in tweets:
        if tweet['text'] in texts:
            continue
        texts.add(tweet['text'])
        results.append(tweet)
    return results

def get_top_tweets(tweets, num_likes=100, num_retweets=100):
    top_likes = sorted(tweets, key=lambda t: int(t['fav_count'] if t['fav_count'] else 0), reverse=True)
    _num_likes = r.randint(len(tweets) // 2, len(tweets)) if num_likes > len(tweets) else num_likes
    top_n_likes = _get_top_tweets_helper(top_likes, _num_likes, 'fav_count')

    top_retweets = sorted(tweets, key=lambda t: int(t['ret_count'] if t['ret_count'] else 0), reverse=True)
    _num_retweets = r.randint(len(tweets) // 2, len(tweets)) if num_retweets > len(tweets) else num_retweets
    top_n_retweets = _get_top_tweets_helper(top_retweets, _num_retweets, 'ret_count')
    
    combined = [*top_n_likes, *top_n_retweets]
    return _remove_duplicates(combined)

def core_summary_function(document, target, lang='en', max_sentence_len=30):
    _target = target[1:]
    nlp = spacy.load(lang)
    # Had to set it to a high value to process large collections of text
    nlp.max_length = NLP_DOC_LENGTH
    nlp_doc = nlp(document)

    hashtag_set = set()
    document_sentences = document.split('\n')
    for line in document_sentences:
        for w in line.split(' '):
            if len(w) > 0 and '#' in w:
                if w[0] == '#':
                    hashtag_set.add(w[1:])
                else:
                    hashtag_set.add(w)

    ### Word frequency table
    # 		dictionary of words and their counts using non stop words

    word_freq = {}
    for word in nlp_doc:
        w = word.text
        w = w.strip(punctuation)
        w = w.lower()
        # stopword omission
        if w not in STOP_WORDS and w not in hashtag_set:
            if w not in word_freq:
                word_freq[w] = 0
            word_freq[w] += 1

    ### Maximum frequency
    max_freq = max(word_freq.items(), key=lambda x: x[1])[1] # recall that the 0th index is the word

    for (word, freq) in word_freq.items():
        word_freq[word] = freq/max_freq

    ### Sentence scores
    # 		scoring every sentence based on the number of words
    # 		(non-stop words in our word freq table)

    sentence_list = [sentence for sentence in nlp_doc.sents]
    seen_sentences = set()

    sent_scores = {}
    for sent in sentence_list:
        # ignore sentences that aren't a certain length
        if len(sent) <= 2:
            continue
        # ignore sentences that repeat the same thing over and over
        if _is_repeat_sentence(sent):
            continue
        # ignore sentences that are duplicates
        if sent.text.strip() in seen_sentences:
            continue
        seen_sentences.add(sent.text.strip())
        for word in sent:
            if word.text == _target:
                continue
            w = word.text.lower()
            if w in word_freq:
                if len(sent.text.split(' ')) < max_sentence_len:
                    if sent not in sent_scores:
                        sent_scores[sent] = 0
                    sent_scores[sent] += word_freq[w]

    summarized_sentences = nlargest(NUM_SENTENCE_SUMMARY, sent_scores, key=sent_scores.get)

    # convert spacy span to string
    final_sentences = [s.text.replace('\n', ' ').replace('.', ' ').strip().capitalize() for s in summarized_sentences]
    final_summary = '. '.join(final_sentences) + '.'
    for pattern, replacement in REPLACE_DICT.items():
        final_summary = re.sub(pattern, replacement, final_summary)

    return final_summary

def summarize_tweets(target, mock):
    '''Summarizes tweets passed in from zeitgeist'''
    selection = sample(target)
    if mock:
        r.shuffle(selection)
        sentences = selection[:NUM_SENTENCE_SUMMARY]
        return ''.join(t['text'] for t in sentences)

    log(f'Summarizing {len(selection)} tweets from {target}...')
    top_n_tweets = get_top_tweets(selection,
                                  num_likes=r.randint(100, 300),
                                  num_retweets=r.randint(100, 300))
    log(f'Selected top {len(top_n_tweets)} tweets')
    corpus = ''.join([row['text'] for row in top_n_tweets])
    summary = core_summary_function(corpus, target)
    return summary

