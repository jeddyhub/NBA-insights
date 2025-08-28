
import argparse
import pandas as pd
from src.nba_synth.synthetic import synthesize_quarters

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/games.csv")
    parser.add_argument("--output", default="data/synthetic_games.csv")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    df_synth = synthesize_quarters(df)
    df_synth.to_csv(args.output, index=False)
    print(f"Synthetic data saved to {args.output}")

if __name__ == "__main__":
    main()
