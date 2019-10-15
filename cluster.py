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

# EXTERNAL LIB
import autocorrect
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import CountVectorizer
from scipy.cluster.hierarchy import dendrogram, linkage

# PROJECT LIB
from extern import *

def filter(text, speller):
    if FILTER_STOPWORDS:
        text = ' '.join([word for word in text.split() if word not in STOPWORDS])
    if CORRECT_SPELLING:
        text = speller(text)
    return text

def find_argcenter(cluster):
    '''Returns the index of the point closest to the mean of the cluster.'''
    mean = np.mean(cluster, axis=0)
    return np.abs(cluster - mean).argmin()

def agglomerate(target):
    log(f'Clustering {target}...')
    
    speller = autocorrect.Speller(lang='en')
    if not os.path.isdir(CACHE_DIR):
        os.mkdir(CACHE_DIR)

    with open(str(DATA_DIR / target) + '.csv.', 'r', newline='', encoding='utf-8') as src_file:
        log('\tReading in data...')
        rdr = csv.reader(src_file)
        raw_data = [row[1] for row in rdr]
        selection = np.random.choice(raw_data, CLUSTERING_SAMPLES)
        corpus = [filter(text, speller) for text in selection]
        
        log('\tVectorizing words...')
        vectorizer = CountVectorizer()
        vectors = vectorizer.fit_transform(corpus).todense()

        log('\tClustering...')
        clustering = AgglomerativeClustering(
            n_clusters=NUM_CLUSTERS, affinity='cosine', memory=str(CACHE_DIR), linkage='complete')
        clustering.fit(vectors)
        
        log('\tFinding centers...')
        cluster_points = [[] for idx in range(NUM_CLUSTERS)]
        cluster_tweets = [[] for idx in range(NUM_CLUSTERS)]
        for idx, (point, label) in enumerate(zip(vectors, clustering.labels_)):
            cluster_points[label].append(point)
            cluster_tweets[label].append(selection[idx])
        
        representatives = []
        for idx in range(NUM_CLUSTERS):
            argcenter = find_argcenter(cluster_points[idx])
            representatives.append(cluster_tweets[idx][argcenter])
        
        log('\t...done.')
        for idx in range(len(representatives)):
            log(f'Representative for label {idx} of size {len(cluster_tweets[idx])}:\n{representatives[idx]}')
        