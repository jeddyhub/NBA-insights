# NBA Synthetic Inequalities — reproducible experiments (CSV version)

## Requirements
- Python 3.9+

## Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Data
Place a `games.csv` file under `data/` with columns: `game_id,date,home_team,away_team,home_pts,away_pts`.

## Run the experiment
```bash
python scripts/run_experiment.py --csv-path data/games.csv --out-report report/report.md
```
