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
    return idx

def agglomerate(target):
    log(f'Clustering {target}...')
    
    # Checking spelling can help normalize text.
    speller = autocorrect.Speller(lang='en')
    if not os.path.isdir(CACHE_DIR):
        os.mkdir(CACHE_DIR)

    # Open the source data file and use it as a corpus for clustering.
    with open(str(DATA_DIR / target) + '.csv.', 'r', newline='', encoding='utf-8') as src_file:
        log('\tReading in data...')
        rdr = csv.reader(src_file)
        raw_data = [row[1] for row in rdr]
        selection = np.random.choice(raw_data, CLUSTERING_SAMPLES)
        corpus = [filter(text, speller) for text in selection]
        
        vectorizer = CountVectorizer()
        vectors = vectorizer.fit_transform(corpus).todense()

        log(f'\tClustering {CLUSTERING_SAMPLES} tweets...')
        clustering = AgglomerativeClustering(
            n_clusters=None,
            affinity='cosine', 
            memory=str(CACHE_DIR),
            compute_full_tree='auto',
            linkage='complete', 
            distance_threshold=DISTANCE_THRESHOLD)
        clustering.fit(vectors)
        
        log('\tFinding centers...')
        cluster_points = [[] for idx in range(len(set(clustering.labels_)))]
        cluster_tweets = [[] for idx in range(len(set(clustering.labels_)))]
        for idx, (point, label) in enumerate(zip(vectors, clustering.labels_)):
            cluster_points[label].append(point)
            cluster_tweets[label].append(selection[idx])

        cluster_points = sorted(cluster_points, key=lambda x: len(x), reverse=True)
        cluster_tweets = sorted(cluster_tweets, key=lambda x: len(x), reverse=True)

        representatives = []
        try:
            for idx in range(NUM_CLUSTERS):
                argcenter = find_argcenter(cluster_points[idx])
                representatives.append(cluster_tweets[idx][argcenter])
        except IndexError:
            log(f'WARNING: There were only {len(set(clustering.labels_))} cluster(s)!')
            pass # There were fewer clusters than NUM_CLUSTERS.
        
        log('\t...done.')
        for idx in range(len(representatives)):
            log(f'From a group of similar tweets of size {len(cluster_tweets[idx])}:\n{representatives[idx]}')
        