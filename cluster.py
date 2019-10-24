#
# authors:
#   Paul Galatic
#
# description:
#   Performs clustering of hashtags.
#

# STD LIB
import os
import csv
import pdb

# EXTERNAL LIB
import autocorrect
import numpy as np
from scipy.spatial import distance
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import CountVectorizer

# PROJECT LIB
from extern import *

def get_stopwords():
    if not os.path.exists(CACHE_DIR / 'stopwords.flag'):
        import nltk
        nltk.download('stopwords')
        open(CACHE_DIR / 'stopwords.flag', 'w').close()
    from nltk.corpus import stopwords
    return set(stopwords.words('english'))

def filter(text, speller):
    if FILTER_STOPWORDS:
        stops = get_stopwords()
        text = ' '.join([word for word in text.split() if word not in stops])
    if CORRECT_SPELLING:
        text = speller(text)
    return text

def find_argcenter(cluster):
    '''Returns the index of the point closest to the mean of the cluster.'''
    center = np.mean(cluster, axis=0)
    closest = None
    least_dist = 1
    for idx in range(len(cluster)):
        dist = distance.cosine(cluster[idx], center)
        if dist < least_dist:
            least_dist = dist
            closest = idx
    return idx, round(1 - least_dist, 2)

def agglomerate(target):
    log(f'Clustering {target}...')
    
    # Checking spelling can help normalize text.
    speller = autocorrect.Speller(lang='en')
    if not os.path.isdir(CACHE_DIR):
        os.mkdir(CACHE_DIR)

    # Open the source data file and use it as a corpus for clustering.
    log('\tReading in data...')
    selection = sample(target)
    corpus = [filter(text, speller) for text in selection]
    
    # Convert tweets into bags-of-words vectors.
    vectorizer = CountVectorizer()
    vectors = vectorizer.fit_transform(corpus).todense()

    # Cluster the vectors using agglomerative clustering over the cosine 
    # similarity space.
    log(f'\tClustering {SAMPLE_SIZE} tweets...')
    clustering = AgglomerativeClustering(
        n_clusters=None,
        affinity='cosine', 
        memory=str(CACHE_DIR),
        compute_full_tree='auto',
        linkage='complete', 
        distance_threshold=DISTANCE_THRESHOLD)
    clustering.fit(vectors)
    
    # Sort the clusters into lists.
    log('\tFinding centers...')
    cluster_points = [[] for idx in range(len(set(clustering.labels_)))]
    cluster_tweets = [[] for idx in range(len(set(clustering.labels_)))]
    for idx, (point, label) in enumerate(zip(vectors, clustering.labels_)):
        cluster_points[label].append(point)
        cluster_tweets[label].append(selection[idx])

    # Sort the lists to find the best ones.
    cluster_points = sorted(cluster_points, key=lambda x: len(x), reverse=True)
    cluster_tweets = sorted(cluster_tweets, key=lambda x: len(x), reverse=True)

    # Find the representative tweets with the least distance to the center
    # of each cluster.
    reps = []
    try:
        for idx in range(NUM_CLUSTERS):
            argcenter, confidence = find_argcenter(cluster_points[idx])
            reps.append((cluster_tweets[idx][argcenter], confidence))
    except IndexError:
        log(f'WARNING: There were only {len(set(clustering.labels_))} cluster(s)!')
        pass # There were fewer clusters than NUM_CLUSTERS.
    
    # Display those reps.
    log('\t...done.')
    for idx in range(len(reps)):
        log(f'Cluster size:\t{len(cluster_tweets[idx])}')
        log(f'Confidence:\t{reps[idx][1]}')
        log(f'Tweet:\t{reps[idx][0]}')
        