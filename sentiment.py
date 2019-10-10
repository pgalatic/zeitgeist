"""

    Main file that will perform sentiment analysis using a python sentiment analysis library 
    called Vader (https://github.com/cjhutto/vaderSentiment).

    Three main tasks: 

    (1) Is the trending topic overall positive, negative or neutral?

    (2) What is the distribution of the sentiment of individual tweets?

    (3) Can we locate particularly "outlier" tweets using sentiment?

    @author Theodora Bendlin

"""
import csv
import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.cluster import DBSCAN, KMeans
from os.path import isfile
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D

DATA_DIR = "data"
FILE_SEPARATOR = "/"
FILE_EXTENSION = ".csv"

K_START = 3
K_END = 15

def reduce_to_indv_tweet_text(target):
    pathname = DATA_DIR + FILE_SEPARATOR + target + FILE_EXTENSION
    if not isfile(pathname):
        print("usage: data file {} does not exist.".format(pathname))
        exit(1)
    
    tweets = []
    with open(pathname) as file:
        reader = csv.reader(file)
        for line in reader:
            tweets.append(line[1])
    
    return tweets

def get_sentiment_data_frame(tweets):
    tweets_map = {
        "tweet": [],
        "compound": [],
        "pos": [],
        "neg": [],
        "neu": []
    }

    analyzer = SentimentIntensityAnalyzer()

    for tweet in tweets:
        tweet_sentiment = analyzer.polarity_scores(tweet)
        tweets_map["tweet"].append(tweet)
        tweets_map["compound"].append(tweet_sentiment["compound"])
        tweets_map["pos"].append(tweet_sentiment["pos"])
        tweets_map["neg"].append(tweet_sentiment["neg"])
        tweets_map["neu"].append(tweet_sentiment["neu"])
    
    return pd.DataFrame(data=tweets_map)

def numerical_sentiment_analysis(tweets_df):

    # Get the average compound score to find out what the overall sentiment is
    avg_compound = tweets_df["compound"].mean()
    if avg_compound >= -0.1 and avg_compound <= 0.1:
        print("Overall Sentiment: Neutral {:0.2f}".format(avg_compound))
    elif avg_compound < -0.1:
        print("Overall Sentiment: Negative {:0.2f}".format(avg_compound))
    else:
        print("Overall Sentiment: Positive {:0.2f}".format(avg_compound))

    # Determine the percentage of positive, negative and neutral tweets to compare with average
    # compound score
    num_tweets = len(tweets_df.index)

    num_pos = (sum([score > 0.1 for score in tweets_df["compound"]]) / num_tweets) * 100
    num_neg = (sum([score < -0.1 for score in tweets_df["compound"]]) / num_tweets) * 100
    num_neu = (sum([(score >= -0.1 and score <= 0.1) for score in tweets_df["compound"]]) / num_tweets * 100)

    print("Positive: {:0.2f}%, Negative: {:0.2f}%, Neutral: {:0.2f}%".format(num_pos, num_neg, num_neu))

    # Determine the ''outlier'' tweets. Currently, defined as the tweets with the highest and lowest
    # compound scores, simplistic definition will be refined once clustering is implemented
    outlier_pos = tweets_df[tweets_df["compound"] == tweets_df["compound"].max()]
    outlier_neg = tweets_df[tweets_df["compound"] == tweets_df["compound"].min()]

    print()

    print("Outlier Positive Tweet: \n", outlier_pos["tweet"].iloc[0])
    print("Outlier Positive Tweet Scores: \n", outlier_pos[["compound", "pos", "neg", "neu"]].iloc[0])
    print()
    print("Outlier Negative Tweet: \n", outlier_neg["tweet"].iloc[0])
    print("Outlier Negative Tweet Scores: \n", outlier_neg[["compound", "pos", "neg", "neu"]].iloc[0])

"""

    There are two types of clustering we are interested in: 

    (1) Clustering tweets by the "intensity" of their sentiment
    (2) Clustering words making up the tweets into sentiment clusters

"""
def sentiment_clustering(tweets_df, debug=False):
    sentiment_vector = tweets_df[['pos', 'neg', 'neu']].values

    k_means_results = run_k_means(sentiment_vector, debug)
    num_kmeans_clusters = k_means_results.labels_.max() + 1
    tweets_df["kmeans_clusters"] = k_means_results.labels_
    plot_clustering_results(tweets_df, "kmeans_clusters", num_kmeans_clusters)
    print_clustering_centroids_data(tweets_df, "kmeans_clusters", num_kmeans_clusters, k_means_results.cluster_centers_)

    dbscan_results = run_dbscan(sentiment_vector)
    num_dbscan_clusters = dbscan_results.labels_.max() + 1
    tweets_df["dbscan_clusters"] = dbscan_results.labels_
    plot_clustering_results(tweets_df, "dbscan_clusters", num_dbscan_clusters)
    print_clustering_centroids_data(tweets_df, "dbscan_clusters", num_dbscan_clusters)

def run_k_means(tweets_df, debug):

    sse = []
    clusters = []

    for k in range(K_START, K_END):
        kmeans_result = KMeans(n_clusters=k, random_state=1).fit(tweets_df)
        clusters.append(kmeans_result)

        if debug:
            sse.append(kmeans_result.inertia_)
            print("k = {}, sse = {}".format(k, kmeans_result.inertia_))
    
    if debug:
        plt.figure()
        plt.plot(np.arange(K_START, K_END), sse)
        plt.xlabel("Number of clusters")
        plt.ylabel("Sum of Squared Errors")
        plt.show()
    
    return clusters[5]

def run_dbscan(tweets_df):
    return DBSCAN(eps=0.015, min_samples=10).fit(tweets_df)

def plot_clustering_results(tweets_df, cluster_label, num_clusters):
    figure = plt.figure()
    axes = figure.add_subplot(111, projection='3d')

    colors = iter(cm.rainbow(np.linspace(0, 1, num_clusters)))
    for n in range(num_clusters):
        cluster_df = tweets_df[tweets_df[cluster_label] == n]
        label = "Cluster {}".format(n)

        x_vals = cluster_df[['pos']].values
        y_vals = cluster_df[['neg']].values
        z_vals = cluster_df[['neu']].values

        axes.scatter(x_vals, y_vals, z_vals, color=next(colors), label=label)

    plt.title("Clustering of Sentiment Distribution")
    axes.set_xlabel("Positive")
    axes.set_ylabel("Negative")
    axes.set_zlabel("Neutral")

    plt.show()

def print_clustering_centroids_data(tweets_df, cluster_label, num_clusters, cluster_centers=None):

    if cluster_centers is None or not cluster_centers.any():
        cluster_centers = []
        for cluster in range(num_clusters):
            cluster_df = tweets_df[tweets_df[cluster_label] == cluster]
            pos = cluster_df[['pos']].values
            neg = cluster_df[['neg']].values
            neu = cluster_df[['neu']].values
            cluster_centers.append((pos.sum() / len(pos), neg.sum() / len(neg), neu.sum() / len(neu)))

    for cluster in range(num_clusters):
        
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

        print("Cluster: ", cluster)
        print("Tweet: ", center_point['tweet'])
        print("Compound: {:0.2f}".format(center_point['compound']))
        print("Positive: {:0.2f}".format(center_point['pos']))
        print("Negative: {:0.2f}".format(center_point['neg']))
        print("Neutral: {:0.2f}".format(center_point['neu']))
        print()

if __name__ == "__main__":

    tweets = reduce_to_indv_tweet_text("#ImpeachTrump")
    tweets_df = get_sentiment_data_frame(tweets)
    print()
    numerical_sentiment_analysis(tweets_df)
    print()
    sentiment_clustering(tweets_df)
    print()