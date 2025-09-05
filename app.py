import streamlit as st
import pandas as pd
import os
import random
import io

# Import core functions
from src.nba_synth.synthetic import synthesize_quarters
from src.nba_synth.features import analyze_features
from src.nba_synth.conjectures import generate_conjectures

# Import insights
from src.nba_synth.insights import (
    conjecture_insight_betting,
    conjecture_insight_coaching,
)

DATA_DIR = "data"

# -----------------------------
# Utility functions
# -----------------------------

def load_dataset(path: str):
    """Safely load a dataset with error handling."""
    if not os.path.exists(path):
        st.error(f"File not found: {path}")
        return None
    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"Error loading {path}: {e}")
        return None

# -----------------------------
# Abbreviation Glossary
# -----------------------------

COLUMN_GLOSSARY = {
    "pf": "Personal Fouls",
    "fta": "Free Throw Attempts",
    "fga": "Field Goal Attempts",
    "fgm": "Field Goals Made",
    "3pa": "3-Point Attempts",
    "3pm": "3-Point Made",
    "ast": "Assists",
    "reb": "Rebounds",
    "blk": "Blocks",
    "stl": "Steals",
    "to": "Turnovers",
    "pts": "Points",
    # add more as needed
}

def explain_columns(df: pd.DataFrame):
    """Return a dict of abbreviations actually present in df."""
    found = {}
    for col in df.columns:
        for abbr, meaning in COLUMN_GLOSSARY.items():
            if abbr.lower() in col.lower():   # case-insensitive match
                found[abbr] = meaning
    return found


# -----------------------------
# Page: Load Database
# -----------------------------

def page_load_data():
    st.header("Load NBA Database")

    # List CSV files
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
    if not files:
        st.warning("No CSV files found in the data directory.")
        return

    dataset_choice = st.radio("Select dataset:", files)

    df = load_dataset(os.path.join(DATA_DIR, dataset_choice))
    if df is not None:
        st.subheader(f"Data Preview: {dataset_choice}")
        st.dataframe(df.head(20))

        st.subheader("Summary Statistics")
        st.write(df.describe())

        # 🆕 Column explanations
        glossary = explain_columns(df)
        if glossary:
            st.subheader("Column Abbreviation Guide")
            for abbr, meaning in glossary.items():
                st.write(f"**{abbr.upper()}**: {meaning}")


# -----------------------------
# Page: Synthesize Data
# -----------------------------

def page_synthesize_data():
    st.header("Synthesize Quarterly Stats")

    st.markdown(
        """
        This step takes the original **per-game box score stats** (e.g., field goal attempts, rebounds, fouls)  
        and generates a **synthetic breakdown by quarter**.  

        - Totals (like rebounds, fouls, turnovers) are split across 4 quarters using a **Dirichlet random split**,  
          so that they add up correctly but vary realistically across quarters.  
        - Paired stats (e.g., `FGA` with `FGM`, `FTA` with `FTM`) are split carefully:  
          first attempts are distributed, then makes are assigned so that **made ≤ attempts** always holds.  
        - Shooting percentages are recomputed per quarter (`fg_pct`, `ft_pct`, etc.).  
        - Finally, **quarterly points** are derived from shot data, ensuring consistency.  

        The result is a dataset that looks like real per-quarter stats, but is generated statistically from the  
        per-game totals. This enables downstream analysis (like feature clustering or inequality conjecturing)  
        at the *quarterly* level, even when raw quarterly stats weren’t originally available.
        """
    )

    df = load_dataset(os.path.join(DATA_DIR, "games.csv"))
    if df is None:
        return

    if st.button("Generate Synthetic Quarterly Stats"):
        with st.spinner("Generating synthetic data..."):
            df_synth = synthesize_quarters(df)
            out_path = os.path.join(DATA_DIR, "synthetic_quarters.csv")
            df_synth.to_csv(out_path, index=False)
        st.success(f"Synthetic data saved to {out_path}")
        st.dataframe(df_synth.head(20))

# -----------------------------
# Page: Feature Analysis
# -----------------------------

def page_feature_analysis():
    st.header("Feature Analysis")

    st.markdown(
        """
        This step reduces the dataset to its most **informative, non-redundant features**.  

        **Steps performed:**
        1. Remove features with **low variance** (near-constant values).  
        2. Drop one of any pair of **highly correlated** features.  
        3. Use **Agglomerative Clustering** on feature correlations to group similar features,  
           then keep one representative from each cluster.  

        The result is a smaller, cleaner feature set, ready for conjecture generation.  
        """
    )

    # Dynamically list datasets in data/ folder, excluding "analyzed" ones
    all_csvs = [
        f for f in os.listdir(DATA_DIR)
        if f.endswith(".csv") and "analyzed" not in f
    ]

    if not all_csvs:
        st.error("No valid datasets found in the data folder.")
        return

    dataset_choice = st.radio("Select a dataset to analyze:", all_csvs)
    df = load_dataset(os.path.join(DATA_DIR, dataset_choice))
    if df is None:
        return

    # Determine save path for analyzed features
    save_path = os.path.join(DATA_DIR, f"{os.path.splitext(dataset_choice)[0]}_analyzed_features.csv")

    # Drop NaN columns
    df = df.dropna(axis=1)
    
    # Remove id columns if present
    extra_columns = ['season_id','team_id_home','team_id_away','video_available_home','team_abbreviation_home','team_name_home','game_id','game_date','matchup_home', 'min', 'video_available_away','season_type']
    for col in extra_columns:
        if col in df.columns:
            df = df.drop(columns=[col])

    bool_cols = df.select_dtypes(include=["bool"]).columns.tolist()

    # Optional filtering for quarterly datasets
    if "synthetic_quarters" in dataset_choice:
        which_features = st.radio(
            "Which features to analyze?",
            ["All numeric features", "Only first half (Q1, Q2) features"],
        )
        if which_features == "All numeric features":
            feats = [c for c in df.select_dtypes(include=["number"]).columns if c not in ["season_id", "game_id"]]
        else:
            feats = [c for c in df.select_dtypes(include=["number"]).columns if "Q3" not in c and "Q4" not in c]
            for drop in ["season_id", "game_id"]:
                if drop in feats:
                    feats.remove(drop)
    else:
        feats = [c for c in df.select_dtypes(include=["number"]).columns if c not in ["season_id", "game_id"]]

    k = st.number_input("How many clusters of features to extract?", min_value=1, value=3, step=1)

    if st.button("Run Feature Analysis"):
        with st.spinner("Analyzing features..."):
            df_analyzed = analyze_features(df[feats], n_clusters=k)

            # Add back boolean cols
            for bcol in bool_cols:
                if bcol in df.columns:
                    df_analyzed[bcol] = df[bcol]

            df_analyzed.to_csv(save_path, index=False)

        st.success(f"Feature analysis saved to {save_path}")
        st.dataframe(df_analyzed.head(20))

        # Download button
        st.download_button(
            "Download Analyzed Features CSV",
            data=df_analyzed.to_csv(index=False),
            file_name=os.path.basename(save_path),
            mime="text/csv",
        )

# -----------------------------
# Page: Generate Conjectures
# -----------------------------

def page_generate_conjectures():
    st.header("Generate Relationships")

    st.markdown(
        """
        TxGraffiti searches for **linear relationships among columns** using optimization (linear programming)
        and heuristics. The approach is described in the paper:  
        **"TxGraffiti — Structured conjecturing over tabular data"**.  
        Read more: [arXiv:2409.19379](https://arxiv.org/pdf/2409.19379)

        This UI exposes the main steps so the process isn't a black box:
        1. choose a dataset and which numeric **features** to search over,  
        2. pick a **target** feature,  
        3. optionally provide **hypotheses** (typically boolean columns),  
        4. choose the generator method (LP), heuristics to filter candidates, and post-processors,
        5. run discovery and inspect/save the resulting conjectures.
        """
    )

    # ---- dataset selection (same mapping as before) ----
    dataset_choice = st.radio(
        "Which dataset do you want to use?",
        [
            "Original games dataset",
            "Synthetic quarterly stats dataset",
            "Analyzed features (original games)",
            "Analyzed features (synthetic)",
        ],
    )

    mapping = {
        "Original games dataset": "games.csv",
        "Synthetic quarterly stats dataset": "synthetic_quarters.csv",
        "Analyzed features (original games)": "analyzed_features.csv",
        "Analyzed features (synthetic)": "synthetic_analyzed_features.csv",
    }

    df = load_dataset(os.path.join(DATA_DIR, mapping[dataset_choice]))
    if df is None:
        return

    # ---- basic preprocessing: drop entirely-NaN columns ----
    df = df.dropna(axis=1)

    numeric_features = [c for c in df.select_dtypes(include=["number"]).columns if c not in ["season_id", "game_id"]]
    boolean_cols = df.select_dtypes(include=["bool"]).columns.tolist()

    st.markdown("**Available numeric features:**")
    st.write(", ".join(numeric_features[:100]) if numeric_features else "*none*")

    # ---- feature selection UI ----
    feat_select_all = st.checkbox("Select all numeric features (recommended for small feature sets)", value=True)
    if feat_select_all:
        selected_features = list(numeric_features)
    else:
        selected_features = st.multiselect("Pick features to search over", numeric_features, default=numeric_features[:10])

    if not selected_features:
        st.warning("Select at least one numeric feature to continue.")
        return

    # ---- target selection ----
    # Encourage user to pick a target from selected features (remove it from "features to search")
    target = st.selectbox("Choose the target feature (the RHS of conjectures)", selected_features)
    # remove the chosen target from the feature set we search over
    features_for_search = [f for f in selected_features if f != target]

    # ---- hypotheses (typically boolean columns) ----
    st.markdown("**Hypotheses (optional)** — typically boolean columns like `home_win` or `away_win`.")
    use_auto_hyps = st.checkbox("Auto-detect boolean columns as hypotheses", value=True)
    if use_auto_hyps:
        hypotheses = list(boolean_cols)
    else:
        hypotheses = st.multiselect("Select hypothesis columns (they must be present in the dataset)", boolean_cols, default=boolean_cols)

    # ---- advanced options: methods, heuristics, post-processors, and runtime limits ----
    with st.expander("Advanced options (methods, heuristics, post-processors, runtime)"):
        st.markdown("**Generator methods** (TxGraffiti generators). Pick at least one; LP is typical.")
        use_lp = st.checkbox("Use linear_programming (LP generator)", value=True)
        use_convex_hull = st.checkbox("Use convex_hull (not recommended for >4 features)", value=False)

        st.markdown("**Heuristics** — functions that accept/reject candidates (filtering).")
        use_morgan = st.checkbox("Use morgan_accept heuristic", value=True)
        use_dalmatian = st.checkbox("Use dalmatian_accept heuristic", value=True)

        st.markdown("**Post-processors** — clean up / sort the discovered conjectures.")
        use_remove_duplicates = st.checkbox("Remove duplicates", value=True)
        use_sort_by_touch = st.checkbox("Sort by touch count (sort_by_touch_count)", value=True)

        st.markdown("**Other options**")
        object_symbol = st.text_input("object_symbol (symbol used in playground, e.g. 'game')", value="game")
        show_top_n = st.number_input("How many top conjectures to display", min_value=1, max_value=200, value=20, step=1)
        max_to_analyze = st.number_input("Maximum conjectures to write/download (full set)", min_value=1, max_value=10000, value=1000, step=1)

    # ---- run discovery ----
    run = st.button("Run Conjecture Discovery")

    if run:
        # lazy import of txgraffiti components and helpful error if missing
        try:
            from txgraffiti.playground import ConjecturePlayground
            from txgraffiti.generators import linear_programming, convex_hull
            from txgraffiti.heuristics import morgan_accept, dalmatian_accept
            from txgraffiti.processing import remove_duplicates, sort_by_touch_count
        except Exception as e:
            st.error(
                "Failed to import txgraffiti. Ensure txgraffiti is installed in your environment.\n\n"
                f"Import error: {e}"
            )
            return

        # assemble the lists based on user choices
        methods = []
        if use_lp:
            methods.append(linear_programming)
        if use_convex_hull:
            methods.append(convex_hull)

        heuristics = []
        if use_morgan:
            heuristics.append(morgan_accept)
        if use_dalmatian:
            heuristics.append(dalmatian_accept)

        post_processors = []
        if use_remove_duplicates:
            post_processors.append(remove_duplicates)
        if use_sort_by_touch:
            post_processors.append(sort_by_touch_count)

        if not methods:
            st.error("Please select at least one generator method (e.g. linear_programming).")
            return

        # Inform user about chosen config
        st.info(
            f"Running TxGraffiti with {len(methods)} method(s), "
            f"{len(heuristics)} heuristic(s), and {len(post_processors)} post-processor(s)."
        )

        # Run discovery inside spinner and handle runtime errors
        try:
            pg = ConjecturePlayground(df, object_symbol=object_symbol)
            conjs = pg.discover(
                methods=methods,
                features=features_for_search,
                target=target,
                hypothesis=hypotheses,
                heuristics=heuristics,
                post_processors=post_processors,
            )
        except Exception as e:
            st.exception(e)
            st.error("TxGraffiti discovery failed. Check the dataset shape and your advanced options.")
            return

        # Normalize to list
        if conjs is None:
            st.warning("No conjectures were returned.")
            return

        # show summary
        st.success(f"Discovery complete — {len(conjs)} conjectures found.")
        st.write(f"Showing top {min(show_top_n, len(conjs))} conjectures:")

        # Display top-N cleanly (use .name when available)
        for c in conjs[:show_top_n]:
            display_text = getattr(c, "name", str(c))
            st.text(display_text)

        # Save all conjectures (up to max_to_analyze) to a UTF-8 text file using .name when available
        out_path = os.path.join(DATA_DIR, "conjectures.txt")
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                for c in conjs[:int(max_to_analyze)]:
                    name = getattr(c, "name", str(c))
                    f.write(name + "\n")
        except Exception as e:
            st.error(f"Failed to write conjectures to disk: {e}")
            return

        st.success(f"Saved up to {max_to_analyze} conjectures to `{out_path}`.")

        # Download button (safely join names)
        download_text = "\n".join(getattr(c, "name", str(c)) for c in conjs[:int(max_to_analyze)])
        st.download_button(
            "Download All Conjectures (text)",
            data=download_text,
            file_name="conjectures.txt",
            mime="text/plain",
        )

# ----------------------------
# Page: Insights
# ----------------------------

import os
import streamlit as st

from src.nba_synth.insights import (
    conjecture_insight_betting,
    conjecture_insight_coaching,
)

def page_gain_insights():
    st.header("💡 Gain Insights from Conjectures")

    st.markdown(
        """
        On this page, the conjectures generated earlier are sent to an **AI insights engine**.  
        Each inequality is interpreted either from a **sports betting** or a **basketball coaching** perspective.  

        This helps you connect the **symbolic patterns** discovered by TxGraffiti with **practical, human-readable insights**.
        """
    )

    # Load conjectures file
    conj_path = os.path.join(DATA_DIR, "conjectures.txt")
    if not os.path.exists(conj_path):
        st.error("No conjectures file found. Please generate conjectures first.")
        return

    with open(conj_path, "r", encoding="utf-8") as f:
        conjectures = [line.strip() for line in f if line.strip()]

    if not conjectures:
        st.warning("The conjectures file is empty.")
        return

    # Perspective choice
    perspective = st.radio(
        "Choose perspective for insights:",
        ["Betting", "Coaching"],
    )

    # Number of conjectures to analyze
    n_to_analyze = st.slider(
        "How many conjectures to analyze?",
        min_value=1,
        max_value=min(20, len(conjectures)),
        value=5,
    )

    show_raw = st.checkbox("Show raw conjectures being analyzed", value=False)

    if show_raw:
        st.markdown("**Conjectures selected for analysis:**")
        for i, conj in enumerate(conjectures[:n_to_analyze], 1):
            st.text(f"{i}. {conj}")

    if st.button("Generate Insights"):
        with st.spinner("Analyzing conjectures with the AI model..."):
            insights = []
            for conj in conjectures[:n_to_analyze]:
                if perspective == "Betting":
                    insight = conjecture_insight_betting(conj)
                else:
                    insight = conjecture_insight_coaching(conj)
                insights.append((conj, insight))

        st.success(f"Generated {len(insights)} insights from a {perspective.lower()} perspective.")

        # Display nicely
        for i, (conj, insight) in enumerate(insights, 1):
            with st.expander(f"Conjecture {i}: {conj}"):
                st.markdown(insight)

        # ✅ Download option for insights
        st.download_button(
            "Download Insights",
            data="\n\n".join(f"{c}\n→ {i}" for c, i in insights),
            file_name="insights.txt",
            mime="text/plain",
        )

# ---------------------------
# Main
# ---------------------------

PAGES = {
    "Load Data": page_load_data,
    "Synthesize Data": page_synthesize_data,
    "Feature Analysis": page_feature_analysis,
    "Inequalities": page_generate_conjectures,
    "Gain Insights": page_gain_insights,
}

def main():
    st.sidebar.title("Navigation")
    choice = st.sidebar.radio("Go to", list(PAGES.keys()))
    PAGES[choice]()

if __name__ == "__main__":
    main()
