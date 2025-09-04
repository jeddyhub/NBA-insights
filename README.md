# NBA Insights

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

## Configure API Key
Rename `OAI_CONFIG_TEMPLATE.json` to `OAI_CONFIG.json`. Enter your OpenAI API key.
