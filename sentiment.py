'''

    Main file that will perform sentiment analysis using a python sentiment analysis library 
    called Vader (https://github.com/cjhutto/vaderSentiment).

    Three main tasks: 

    (1) Is the trending topic overall positive, negative or neutral?

    (2) What is the distribution of the sentiment of individual tweets?

    (3) Can we locate particularly 'outlier' tweets using sentiment?

    @author Theodora Bendlin

'''
import csv
import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.cluster import DBSCAN, KMeans
from os.path import isfile
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D
from extern import *

"""

    Main method that will find the main (6) cluster representations for
    a target file:
    - The most positive, negative and neutral clusters
    - The largest clusters (exclusive from previous group)

    @parameter target (str) target data file
    @parameter mock (boolean) true if random tweets should be chosen, false otherwise
    @parameter cluster_method (str) which type of clustering to use, kmeans or dbscan
    @parameter debug (boolean) if debug mode for kmeans clustering mode should be enabled
    @parameter plot_clusters (boolean) if cluster plot should show up

    @return (object) reps representation for representative tweets
"""
def find_sentiment_cluster_reps(target, mock, cluster_method='kmeans', debug=False, plot_clusters=False):
    log(f'Performing sentiment analysis on {target}...')

    # Uses a subsample of the data as in cluster.py
    log('\tReading in data...')
    t_sample = sample(target)

    # If mocking the data, use a random sample
    if mock:
        subsamp = t_sample[np.random.choice(t_sample.shape[0], 6)]
        reps = [[0, np.random.uniform(0.5), item] for item in subsamp]

        # Using the actual sentiment analyzer so its not as obvious that the
        # tweet reps are randomly generated
        analyzer = SentimentIntensityAnalyzer()

        idx = 0
        for row in subsamp:
            sentiment = analyzer.polarity_scores(row['text'])
            reps[idx][1] = sentiment['compound']
            idx += 1

        # Mock cluster sizes so they appear reasonable.
        reps[0][0] = np.random.randint(SAMPLE_SIZE / 5, SAMPLE_SIZE / 3)
        reps[1][0] = np.random.randint(SAMPLE_SIZE / 10, SAMPLE_SIZE / 3)
        reps[2][0] = np.random.randint(SAMPLE_SIZE / 8, SAMPLE_SIZE / 3)
        reps[3][0] = np.random.randint(SAMPLE_SIZE / 5, SAMPLE_SIZE / 1.5)
        reps[4][0] = np.random.randint(SAMPLE_SIZE / 5, SAMPLE_SIZE / 2)
        reps[5][0] = np.random.randint(SAMPLE_SIZE / 2, SAMPLE_SIZE / 1.5)

        # Sort the first three into pos, neg, neutral
        reps[:3] = sorted(reps[:3], key=lambda x: x[1], reverse=True)
        temp = reps[2]
        reps[2] = reps[1]
        reps[1] = temp

        # Sort the last (3) by size
        reps[3:] = sorted(reps[3:], key=lambda x: x[0], reverse=True)

        return reps


    # Converts tweets sample to dataframe of tweets with sentiment values
    sentiment_df = get_sentiment_data_frame(t_sample)

    # Just do one type of clustering, passed in as optional command line arg
    clustering = None
    if cluster_method == 'kmeans':
        clustering = run_k_means(sentiment_df[['pos', 'neg', 'neu']].values, debug)
    else:
        clustering = run_dbscan(sentiment_df[['pos', 'neg', 'neu']].values)

    sentiment_df['cluster_label'] = clustering.labels_
    if plot_clusters:
        plot_clustering_results(sentiment_df, clustering.labels_.max() + 1, plot_title="Sentiment Clustering Using " + cluster_method)

    # Collect cluster and centermoid point data into one dataframe
    cluster_df = get_cluster_centers_info(sentiment_df, list(range(0, clustering.labels_.max() + 1)))
    
    # Gets the top 3 extreme clusters (most pos, neg, neu) and the largest 3
    # clusters that not any of the most extreme
    extreme_clusters = get_most_extreme_clusters(cluster_df)
    largest_clusters = get_k_largest_clusters(cluster_df, excluded_clusters=extreme_clusters)

    # Returning reps representation from cluster.py
    return convert_to_reps(t_sample, [extreme_clusters, largest_clusters])

'''
    Calculates the sentiment values using the vader library for
    each tweet and stores it in a pandas dataframe for analysis
    and manipulation. The scores from vader are as follows:

    compound - the overall sentiment score of the tweet [-1, 1]
    pos - the amount of the tweet that has positive sentiment [0, 1]
    neg - the amount of the tweet that has negative sentiment [0, 1]
    neu - the amount of the tweet that has neutral sentiment [0, 1]

    @param t_sample (list) subsample of tweets
    @returns (Dataframe) pandas dataframe of tweets and sentiment values
'''
def get_sentiment_data_frame(t_sample):
    tweets = [row['text'] for row in t_sample]

    tweets_map = {
        'tweet_idx': [],
        'compound': [],
        'pos': [],
        'neg': [],
        'neu': []
    }

    # Sentiment analysis object from Vader
    analyzer = SentimentIntensityAnalyzer()

    count = 0
    for tweet in tweets:
        tweet_sentiment = analyzer.polarity_scores(tweet)
        tweets_map['compound'].append(tweet_sentiment['compound'])
        tweets_map['pos'].append(tweet_sentiment['pos'])
        tweets_map['neg'].append(tweet_sentiment['neg'])
        tweets_map['neu'].append(tweet_sentiment['neu'])

        tweets_map['tweet_idx'].append(count)
        count += 1
    
    return pd.DataFrame(data=tweets_map)

'''
    Helper method that will run KMeans on the twitter dataframe.

    To choose best number of clusters, this method should be run with
    debug set to true so that the SSE plot is shown. The BEST_K_IDX
    global parameter can be adjusted to show the clusters for a given
    'k', where

    idx     0 1 2 3 ...
    k       3 4 5 6 ...

    @param tweets_df (Dataframe) dataframe of tweets and sentiment scores
    @param debug (boolean) flag for printing out kmeans information
'''
def run_k_means(tweets_df, debug):

    sse = []
    clusters = []

    if debug:
        for k in range(K_START, K_END):
            kmeans_result = KMeans(n_clusters=k, random_state=1).fit(tweets_df)
            clusters.append(kmeans_result)

            sse.append(kmeans_result.inertia_)
            log(f'k = {k}, sse = {kmeans_result.inertia_}')
        
        plt.figure()
        plt.plot(np.arange(K_START, K_END), sse)
        plt.xlabel('Number of clusters')
        plt.ylabel('Sum of Squared Errors')
        plt.show()
        
        # TODO: Which cluster is actually the best?
        clusters[BEST_K_IDX]
    
    else:
        return KMeans(n_clusters=DEFAULT_NUM_CLUSTERS, random_state=1).fit(tweets_df)

'''
    Runs the DBSCAN algorithm. Separate function for consistency
    and to support additional operations later on.

    @param tweets_df (Dataframe) dataframe of tweets and sentiment scores
'''
def run_dbscan(tweets_df):
    return DBSCAN(eps=0.015, min_samples=10).fit(tweets_df)

'''
    Helper function that will plot the clustering results
    using the matplotlib library.

    @param tweets_df (Dataframe) dataframe of tweets and sentiment scores
    @param num_clusters (int) the number of clusters for the label
'''
def plot_clustering_results(tweets_df, num_clusters, plot_title="Clustering of Sentiment Distribution"):
    figure = plt.figure()
    axes = figure.add_subplot(111, projection='3d')

    colors = iter(cm.rainbow(np.linspace(0, 1, num_clusters)))
    for n in range(num_clusters):
        cluster_df = tweets_df[tweets_df['cluster_label'] == n]
        label = 'Cluster {}'.format(n)

        x_vals = cluster_df[['pos']].values
        y_vals = cluster_df[['neg']].values
        z_vals = cluster_df[['neu']].values

        axes.scatter(x_vals, y_vals, z_vals, color=next(colors), label=label)

    plt.title(plot_title)
    axes.set_xlabel('Positive')
    axes.set_ylabel('Negative')
    axes.set_zlabel('Neutral')

    plt.show()

"""

    Finds the tweet closest to the cluster centers and returns a dataframe
    with cluster info as well as some useful debugging information.

    @parameter tweets_df (Pandas dataframe) dataframe with cluster assignments
        and sentiment values
    @parameter clusters (array) int array 0 - n, the number of clusters

    @returns (Pandas dataframe) cluster info dataframe
"""
def get_cluster_centers_info(tweets_df, clusters):

    # Determines what the cluster centers should be
    # Defined as the averages for pos, neg, and neu for all the points in the cluster
    cluster_centers = []
    for cluster in range(len(clusters)):
        cluster_df = tweets_df[tweets_df['cluster_label'] == cluster]
        cluster_size = len(cluster_df)

        compound = cluster_df[['compound']].values
        pos = cluster_df[['pos']].values
        neg = cluster_df[['neg']].values
        neu = cluster_df[['neu']].values

        cluster_centers.append((compound.sum() / cluster_size, pos.sum() / cluster_size, neg.sum() / cluster_size, neu.sum() / cluster_size))

    # Creating a separate dataframe to keep track of cluster stats
    cluster_info_df = {
        'overall_compound': [],
        'overall_pos': [],
        'overall_neg': [],
        'overall_neu': [],
        'center_tweet_id': [],
        'center_compound': [],
        'center_pos': [],
        'center_neg': [],
        'center_neu': [],
        'cluster_size': [],
        'cluster_label': []
    }

    for cluster in clusters:
        
        centroid = cluster_centers[cluster]
        cluster_points = tweets_df[tweets_df['cluster_label'] == cluster]

        min_distance = float('inf')
        center_point = None
        for _, row in cluster_points.iterrows():
            point = row[['pos', 'neg', 'neu']].values
            point_dist = np.linalg.norm((point-centroid[1:]))
            if point_dist < min_distance:
                min_distance = point_dist
                center_point = row

        cluster_info_df['overall_compound'].append(centroid[0])
        cluster_info_df['overall_pos'].append(centroid[1])
        cluster_info_df['overall_neg'].append(centroid[2])
        cluster_info_df['overall_neu'].append(centroid[3])

        cluster_info_df['center_tweet_id'].append(center_point['tweet_idx'])
        cluster_info_df['center_compound'].append(center_point['compound'])
        cluster_info_df['center_pos'].append(center_point['pos'])
        cluster_info_df['center_neg'].append(center_point['neg'])
        cluster_info_df['center_neu'].append(center_point['neu'])

        cluster_info_df['cluster_label'].append(cluster)
        cluster_info_df['cluster_size'].append(len(cluster_points))
    
    return pd.DataFrame(data=cluster_info_df)

"""

    Gets the "most extreme" clusters using the cluster
    info dataframe.

    @parameter cluster_info_df (pandas dataframe) cluster info

    @returns (pandas dataframe)
"""
def get_most_extreme_clusters(cluster_info_df):
    pos_sort = cluster_info_df.ix[(cluster_info_df['overall_compound'] - 1).abs().argsort()[:1]]
    neg_sort = cluster_info_df.ix[(cluster_info_df['overall_compound'] + 1).abs().argsort()[:1]]
    neu_sort = cluster_info_df.ix[(cluster_info_df['overall_compound'] - 0).abs().argsort()[:1]]

    return pd.concat([pos_sort, neg_sort, neu_sort])

"""

    Gets the largest clusters, exclusive from the list passed in using
    the cluster info dataframe.

    @parameter cluster_info_df (pandas dataframe) cluster info
    @parameter excluded_clusters (array) array of clusters to remove from consideration
    @parameter k (int) max number of clusters to return

    @returns (pandas dataframe)
"""
def get_k_largest_clusters(cluster_info_df, excluded_clusters, k=MAX_PRINTED_CLUSTERS):
    sorted_clusters = cluster_info_df.sort_values('cluster_size', ascending=False)
    excluded_cluster_labels = excluded_clusters[['cluster_label']].values.flatten()
    
    return sorted_clusters[~sorted_clusters['cluster_label'].isin(excluded_cluster_labels)].head(k)

"""

    Converts the cluster dataframe info view into the representation
    expected by the module calling the sentiment functionality.

    Expected form: 
        (1) cluster size,
        (2)compound score for the tweet representing the center,
        (3) tweet rep, original representation from the sample
    
    @parameter t_sample (array) array of ordered dict objects representing tweets
    @parameter cluster_dfs (array) array of cluster dataframes to return

    @return reps (array) tuples of tweet info
"""
def convert_to_reps(t_sample, cluster_dfs):
    reps = []
    for cluster_df in cluster_dfs:
        for _, cluster in cluster_df.iterrows():
            cluster_rep = []
            cluster_rep.append(cluster['cluster_size'])
            cluster_rep.append(cluster['center_compound'])
            cluster_rep.append(t_sample[int(cluster['center_tweet_id'])])
            reps.append(cluster_rep)
    
    return reps