
import pandas as pd
import numpy as np

# Stats to split by quarter (grouped for percentages)
# Note: we removed 'pts' since it will be derived
split_stats = {
    'fga': 'fgm',
    'fg3a': 'fg3m',
    'fta': 'ftm',
    'oreb': None,
    'dreb': None,
    'ast': None,
    'stl': None,
    'blk': None,
    'tov': None,
    'pf': None
}

quarters = ['Q1', 'Q2', 'Q3', 'Q4']


def split_total(value, n=4):
    """Split a total integer value across n parts using Dirichlet proportions (rounded)."""
    if pd.isna(value) or value == 0:
        return [0] * n
    value = int(round(value))  # ensure integer
    proportions = np.random.dirichlet(np.ones(n), size=1)[0]
    split = np.floor(proportions * value).astype(int)
    diff = value - split.sum()
    for i in range(abs(diff)):
        split[i % n] += np.sign(diff)
    return split.tolist()


def split_attempts_and_made(attempts_total, made_total):
    """Split attempts first, then allocate made ≤ attempts each quarter."""
    attempts_total = int(round(attempts_total)) if not pd.isna(attempts_total) else 0
    made_total = int(round(made_total)) if not pd.isna(made_total) else 0

    attempts_split = split_total(attempts_total, 4)

    if made_total > attempts_total:
        made_total = attempts_total  # safety check

    made_split = [0] * 4
    if made_total > 0:
        proportions = np.random.dirichlet(np.ones(4), size=1)[0]
        raw = np.floor(proportions * made_total).astype(int)
        diff = made_total - raw.sum()
        for i in range(abs(diff)):
            raw[i % 4] += np.sign(diff)

        # Clip by attempts
        for i in range(4):
            made_split[i] = min(raw[i], attempts_split[i])

        # If we clipped too much, redistribute remaining makes
        leftover = made_total - sum(made_split)
        while leftover > 0:
            for i in np.random.permutation(4):
                if made_split[i] < attempts_split[i]:
                    made_split[i] += 1
                    leftover -= 1
                    if leftover == 0:
                        break

    return attempts_split, made_split

def synthesize_quarters(df: pd.DataFrame) -> pd.DataFrame:
    """Generate synthetic per-quarter stats from per-game stats."""
    # Ensure input DataFrame has necessary columns
    required_cols = ['season_id', 'game_id', 'game_date', 'matchup_home', 'wl_home', 'wl_away']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Input DataFrame must contain '{col}' column.")

    rows = []

    for _, row in df.iterrows():
        game_data = {
            'season_id': row['season_id'],
            'game_id': row['game_id'],
            'game_date': row['game_date'],
            'matchup': row['matchup_home'],
            'home_win': row['wl_home'] == 'W',
            'away_win': row['wl_away'] == 'W'
        }

        for team in ['home', 'away']:
            for stat, made_stat in split_stats.items():
                stat_val = row.get(f'{stat}_{team}', 0)
                stat_val = int(round(stat_val)) if not pd.isna(stat_val) else 0

                if made_stat:  # paired stat, like fgm with fga
                    made_val = row.get(f'{made_stat}_{team}', 0)
                    made_val = int(round(made_val)) if not pd.isna(made_val) else 0

                    attempts_split, made_split = split_attempts_and_made(stat_val, made_val)

                    for i, q in enumerate(quarters):
                        game_data[f'{q}_{team}_{stat}'] = attempts_split[i]
                        game_data[f'{q}_{team}_{made_stat}'] = made_split[i]

                        pct_name = f'{q}_{team}_{stat[:2]}_pct'
                        if attempts_split[i] > 0:
                            game_data[pct_name] = round(made_split[i] / attempts_split[i], 3)
                        else:
                            game_data[pct_name] = None
                else:  # standalone stat
                    values = split_total(stat_val)
                    for i, q in enumerate(quarters):
                        game_data[f'{q}_{team}_{stat}'] = values[i]

            # Now compute points per quarter consistently
            for i, q in enumerate(quarters):
                fgm = int(game_data.get(f'{q}_{team}_fgm', 0))
                fg3m = int(game_data.get(f'{q}_{team}_fg3m', 0))
                ftm = int(game_data.get(f'{q}_{team}_ftm', 0))

                pts = 2 * (fgm - fg3m) + 3 * fg3m + ftm
                game_data[f'{q}_{team}_pts'] = pts

        rows.append(game_data)

    # Create the final DataFrame
    df_synth = pd.DataFrame(rows)
    
    # save as csv
    df_synth.to_csv("data/synthetic_quarters.csv", index=False)
    
    return df_synth