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
# Page: Load Data
# -----------------------------

def page_load_data():
    st.header("📂 Load NBA Data")

    dataset_choice = st.radio(
        "Select dataset:",
        ["Original games dataset", "Synthetic quarterly stats dataset"],
    )

    if dataset_choice == "Original games dataset":
        df = load_dataset(os.path.join(DATA_DIR, "games.csv"))
    else:
        df = load_dataset(os.path.join(DATA_DIR, "synthetic_quarters.csv"))

    if df is not None:
        st.subheader("Data Preview")
        st.dataframe(df.head(20))

        st.subheader("Summary Statistics")
        st.write(df.describe())

        st.subheader("Dataset Info")
        buffer = io.StringIO()
        df.info(buf=buffer)
        st.text(buffer.getvalue())

# -----------------------------
# Page: Synthesize Data
# -----------------------------

def page_synthesize_data():
    st.header("⚙️ Synthesize Quarterly Stats")

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
    st.header("📊 Feature Analysis")

    dataset_choice = st.radio(
        "Which dataset do you want to analyze?",
        ["Original games dataset", "Synthetic quarterly stats dataset"],
    )

    if dataset_choice == "Original games dataset":
        df = load_dataset(os.path.join(DATA_DIR, "games.csv"))
        save_path = os.path.join(DATA_DIR, "analyzed_features.csv")
    else:
        df = load_dataset(os.path.join(DATA_DIR, "synthetic_quarters.csv"))
        save_path = os.path.join(DATA_DIR, "synthetic_analyzed_features.csv")

    if df is None:
        return

    # Drop NaN columns like in CLI
    df = df.dropna(axis=1)

    bool_cols = df.select_dtypes(include=["bool"]).columns.tolist()

    if dataset_choice == "Synthetic quarterly stats dataset":
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

    k = st.number_input("How many features to project onto?", min_value=1, value=3, step=1)

    if st.button("Run Feature Analysis"):
        with st.spinner("Analyzing features..."):
            df_analyzed = analyze_features(df[feats], n_clusters=k)

            # add back boolean cols
            for bcol in bool_cols:
                if bcol in df.columns:
                    df_analyzed[bcol] = df[bcol]

            df_analyzed.to_csv(save_path, index=False)

        st.success(f"Feature analysis saved to {save_path}")
        st.dataframe(df_analyzed.head(20))

        # Allow user to download immediately
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
    st.header("🤔 Generate Conjectures")

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

    df = df.dropna(axis=1)

    features = [c for c in df.select_dtypes(include=["number"]).columns if c not in ["season_id", "game_id"]]
    bool_cols = df.select_dtypes(include=["bool"]).columns.tolist()

    target_type = st.radio(
        "Target feature selection",
        ["Randomly select", "Specify manually"],
    )

    if target_type == "Specify manually":
        target = st.selectbox("Select target feature:", features)
    else:
        target = random.choice(features)
        st.info(f"Randomly selected target feature: {target}")

    # ensure target not in features list
    if target in features:
        features.remove(target)

    if st.button("Generate Conjectures"):
        with st.spinner("Generating conjectures..."):
            conjectures = generate_conjectures(df, features, target, bool_cols)

        st.success(f"{len(conjectures)} conjectures generated.")

        # ✅ Display top conjectures cleanly
        st.subheader("Top Conjectures")
        for conj in conjectures[:20]:
            st.text(conj.name)   # st.text keeps plain text formatting

        # ✅ Save all conjectures as UTF-8 plain text
        out_path = os.path.join(DATA_DIR, "conjectures.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            for c in conjectures:
                f.write(c.name + "\n")

        # ✅ Download option
        st.download_button(
            "Download All Conjectures",
            data="\n".join(c.name for c in conjectures),
            file_name="conjectures.txt",
            mime="text/plain",
        )
        
# ----------------------------
# Page: Insights
# ----------------------------

def page_gain_insights():
    st.header("💡 Gain Insights from Conjectures")

    # Load conjectures from text file
    file_path = os.path.join(DATA_DIR, "conjectures.txt")
    if not os.path.exists(file_path):
        st.error("No conjectures file found. Please generate conjectures first.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        conjectures = [line.strip() for line in f if line.strip()]

    if not conjectures:
        st.warning("The conjectures file is empty. Generate conjectures first.")
        return

    # Perspective choice
    perspective = st.radio(
        "Choose perspective for insights:",
        ["Betting", "Coaching"],
    )

    # Number of conjectures to analyze
    num_to_analyze = st.slider(
        "How many conjectures do you want to analyze?",
        min_value=1,
        max_value=min(20, len(conjectures)),
        value=5,
    )

    if st.button("Generate Insights"):
        with st.spinner("Analyzing conjectures..."):
            results = []
            for conj in conjectures[:num_to_analyze]:
                if perspective == "Betting":
                    insight = conjecture_insight_betting(conj)
                else:
                    insight = conjecture_insight_coaching(conj)
                results.append((conj, insight))

        st.success(f"Generated {len(results)} insights from a {perspective.lower()} perspective.")

        # Display results nicely
        for i, (conj, insight) in enumerate(results, 1):
            with st.expander(f"Conjecture {i}: {conj}"):
                st.write(insight)

# ---------------------------
# Main
# ---------------------------

PAGES = {
    "Load Data": page_load_data,
    "Synthesize Data": page_synthesize_data,
    "Feature Analysis": page_feature_analysis,
    "Inequalities": page_generate_conjectures,
    "Gain Insights": page_gain_insights,   # ✅ New option
}

def main():
    st.sidebar.title("Navigation")
    choice = st.sidebar.radio("Go to", list(PAGES.keys()))
    PAGES[choice]()

if __name__ == "__main__":
    main()
