
import argparse
import pandas as pd
from src.nba_synth.features import analyze_features
from src.nba_synth.conjectures import generate_conjectures

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/synthetic_games.csv")
    parser.add_argument("--clusters", type=int, default=3)
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    features = analyze_features(df, n_clusters=args.clusters)

    conjectures = generate_conjectures(features)
    print("Generated Conjectures:")
    for c in conjectures:
        print("-", c)

if __name__ == "__main__":
    main()
