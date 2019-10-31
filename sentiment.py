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

'''
    Retrieves the tweets from a given .csv file. DEPRECATED.

    @parameter target (string) filename
    @returns (list) list of tweets
'''
def reduce_to_indv_tweet_text(target, mock):
    pathname = str(DATA_DIR / target) + '.csv'
    if not isfile(pathname):
        log(f'data file {pathname} does not exist.')
        exit(1)
    
    tweets = []
    with open(pathname) as file:
        reader = csv.reader(file)
        for line in reader:
            tweets.append(line[1])
    
    return tweets

'''
    Calculates the sentiment values using the vader library for
    each tweet and stores it in a pandas dataframe for analysis
    and manipulation. The scores from vader are as follows:

    compound - the overall sentiment score of the tweet [-1, 1]
    pos - the amount of the tweet that has positive sentiment [0, 1]
    neg - the amount of the tweet that has negative sentiment [0, 1]
    neu - the amount of the tweet that has neutral sentiment [0, 1]

    @param tweets (list) list of tweet text
    @returns (Dataframe) pandas dataframe of tweets and sentiment values
'''
def get_sentiment_data_frame(target):
    tweets = [row['text'] for row in sample(target)]

    tweets_map = {
        'tweet': [],
        'compound': [],
        'pos': [],
        'neg': [],
        'neu': []
    }

    analyzer = SentimentIntensityAnalyzer()

    for tweet in tweets:
        tweet_sentiment = analyzer.polarity_scores(tweet)
        tweets_map['tweet'].append(tweet)
        tweets_map['compound'].append(tweet_sentiment['compound'])
        tweets_map['pos'].append(tweet_sentiment['pos'])
        tweets_map['neg'].append(tweet_sentiment['neg'])
        tweets_map['neu'].append(tweet_sentiment['neu'])
    
    return pd.DataFrame(data=tweets_map)

'''
    Computes several values for numerical analysis, including:

    - Average compound score
    - Percentage values of positive/negative/neutral tweets
    - 'outlier' sentiment tweets, i.e. those with extreme positive or
    negative values

    @param tweets_df (Dataframe) dataframe of tweets and sentiment scores
'''
def numerical_sentiment_analysis(tweets_df, mock):

    # Get the average compound score to find out what the overall sentiment is
    avg_compound = tweets_df['compound'].mean()
    if avg_compound >= -NEUTRAL_CUTOFF and avg_compound <= NEUTRAL_CUTOFF:
        log(f'Overall Sentiment: Neutral {avg_compound:.2f}')
    elif avg_compound < -NEUTRAL_CUTOFF:
        log(f'Overall Sentiment: Negative {avg_compound:.2f}')
    else:
        log(f'Overall Sentiment: Positive {avg_compound:.2f}')

    # Determine the percentage of positive, negative and neutral tweets to compare with average
    # compound score
    num_tweets = len(tweets_df.index)

    num_pos = (sum([score > NEUTRAL_CUTOFF for score in tweets_df['compound']]) / num_tweets) * 100
    num_neg = (sum([score < -NEUTRAL_CUTOFF for score in tweets_df['compound']]) / num_tweets) * 100
    num_neu = (sum([(score >= -NEUTRAL_CUTOFF and score <= NEUTRAL_CUTOFF) for score in tweets_df['compound']]) / num_tweets * 100)

    log(f'Positive: {num_pos}%, Negative: {num_neg}%, Neutral: {num_neu}%')

    # Determine the ''outlier'' tweets. Currently, defined as the tweets with the highest and lowest
    # compound scores, simplistic definition will be refined once clustering is implemented
    outlier_pos = tweets_df[tweets_df['compound'] == tweets_df['compound'].max()]
    outlier_neg = tweets_df[tweets_df['compound'] == tweets_df['compound'].min()]

    log('Outlier Positive Tweet: \n', outlier_pos['tweet'].iloc[0])
    log('Outlier Positive Tweet Scores: \n', outlier_pos[['compound', 'pos', 'neg', 'neu']].iloc[0])
    log('Outlier Negative Tweet: \n', outlier_neg['tweet'].iloc[0])
    log('Outlier Negative Tweet Scores: \n', outlier_neg[['compound', 'pos', 'neg', 'neu']].iloc[0])

'''
    Performs two types of clustering approaches:

    (1) Clustering tweets by the 'intensity' of their sentiment
    (2) Clustering words making up the tweets into sentiment clusters

    For (1) KMeans and DBSCAN are used to compare results of different
    clustering algorithms.

    (2) is in progress

    @param tweets_df (Dataframe) dataframe of tweets and sentiment scores
    @param debug (boolean) flag for printing out kmeans information
'''
def sentiment_clustering(tweets_df, mock, debug=False, plot_clusters=False):
    sentiment_vector = tweets_df[['pos', 'neg', 'neu']].values

    k_means_results = run_k_means(sentiment_vector, debug)
    num_kmeans_clusters = k_means_results.labels_.max() + 1
    tweets_df['kmeans_clusters'] = k_means_results.labels_
    print_clustering_centroids_data(tweets_df, 'kmeans_clusters', num_kmeans_clusters, k_means_results.cluster_centers_)

    dbscan_results = run_dbscan(sentiment_vector)
    num_dbscan_clusters = dbscan_results.labels_.max() + 1
    tweets_df['dbscan_clusters'] = dbscan_results.labels_
    print_clustering_centroids_data(tweets_df, 'dbscan_clusters', num_dbscan_clusters)

    if plot_clusters:
        plot_clustering_results(tweets_df, 'kmeans_clusters', num_kmeans_clusters, plot_title="K-Means Numerical Sentiment Clustering Results")
        plot_clustering_results(tweets_df, 'dbscan_clusters', num_dbscan_clusters, plot_title="DBSCAN Numerical Sentiment Clustering Results")

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
        return KMeans(n_clusters=BEST_K_IDX, random_state=1).fit(tweets_df)

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
    @param cluster_label (string) pandas dataframe key for clustering results
    @param num_clusters (int) the number of clusters for the label
'''
def plot_clustering_results(tweets_df, cluster_label, num_clusters, plot_title="Clustering of Sentiment Distribution"):
    figure = plt.figure()
    axes = figure.add_subplot(111, projection='3d')

    colors = iter(cm.rainbow(np.linspace(0, 1, num_clusters)))
    for n in range(num_clusters):
        cluster_df = tweets_df[tweets_df[cluster_label] == n]
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

'''
    Prints the tweets at the center of the biggest clusters.

    Since KMeans result supplies the coordinates of these centroids already, there is an optional
    param for this field to pass in a pre-computed list of centroids.

    The tweet chosen is the one that is closest to the calculated centroids.

    @param tweets_df (Dataframe) dataframe of tweets and sentiment scores
    @param cluster_label (string) pandas dataframe key for clustering results
    @param num_clusters (int) the number of clusters for the label
    @param cluster_centers (list) list of centroid coordinates
'''
def print_clustering_centroids_data(tweets_df, cluster_label, num_clusters, cluster_centers=None):

    log('Printing out the largest clusters...')
    if cluster_centers is None or not cluster_centers.any():
        cluster_centers = []
        for cluster in range(num_clusters):
            cluster_df = tweets_df[tweets_df[cluster_label] == cluster]
            pos = cluster_df[['pos']].values
            neg = cluster_df[['neg']].values
            neu = cluster_df[['neu']].values
            cluster_centers.append((pos.sum() / len(pos), neg.sum() / len(neg), neu.sum() / len(neu)))

    biggest_clusters = get_k_biggest_clusters(tweets_df, cluster_label, num_clusters)
    for cluster in biggest_clusters:
        
        centroid = cluster_centers[cluster]
        cluster_points = tweets_df[tweets_df[cluster_label] == cluster]

        min_distance = float('inf')
        center_point = None
        for _, row in cluster_points.iterrows():
            point = row[['pos', 'neg', 'neu']].values
            point_dist = np.linalg.norm((point-centroid))
            if point_dist < min_distance:
                min_distance = point_dist
                center_point = row

        log('Tweet: ', center_point['tweet'])
        log('Compound: ', center_point['compound'])
        log('Positive: ', center_point['pos'])
        log('Negative: ', center_point['neg'])
        log('Neutral: ', center_point['neu'])

"""
    Helper function that will get the biggest k clusters, on default set to global
    constant.

    @param tweets_df (Dataframe) dataframe of tweets and sentiment scores
    @param cluster_label (string) pandas dataframe key for clustering results
    @param num_clusters (int) the number of clusters for the label
"""
def get_k_biggest_clusters(tweets_df, cluster_label, num_clusters, k=MAX_PRINTED_CLUSTSERS):
    cluster_sizes = {}
    for cluster in range(num_clusters):
        cluster_sizes[cluster] = len(tweets_df[tweets_df[cluster_label] == cluster])
    
    biggest_clusters = []
    smallest_cluster = -1
    for cluster_key in cluster_sizes:
        if len(biggest_clusters) < k:
            biggest_clusters.append(cluster_key)
            if smallest_cluster == -1 or cluster_sizes[smallest_cluster] > cluster_sizes[cluster_key]:
                smallest_cluster = cluster_key
        else:
            if cluster_sizes[cluster_key] < cluster_sizes[smallest_cluster]:
                continue

            biggest_clusters.remove(smallest_cluster)
            biggest_clusters.append(cluster_key)
            smallest_cluster = cluster_key
            for cluster in biggest_clusters:
                if cluster_sizes[cluster_key] < cluster_sizes[smallest_cluster]:
                    smallest_cluster = cluster_key
    return biggest_clusters

if __name__ == '__main__':

    tweets = reduce_to_indv_tweet_text('#ImpeachTrump')
    tweets_df = get_sentiment_data_frame(tweets)
    numerical_sentiment_analysis(tweets_df)
    sentiment_clustering(tweets_df, plot_clusters=True)