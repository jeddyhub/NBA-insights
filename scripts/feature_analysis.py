
import argparse
import pandas as pd
from src.nba_synth.features import analyze_features

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/synthetic_games.csv")
    parser.add_argument("--clusters", type=int, default=None,
                        help="Number of clusters (if None, will prompt user)")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    k = args.clusters
    if k is None:
        k = int(input("How many features/clusters do you want to focus on? "))

    results = analyze_features(df, n_clusters=k)
    print("Feature analysis complete. Cluster summary:")
    print(results.head())

if __name__ == "__main__":
    main()
