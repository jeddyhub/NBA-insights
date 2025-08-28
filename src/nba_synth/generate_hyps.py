import pandas as pd

def generate_hyps(df: pd.DataFrame) -> pd.DataFrame:
    """Generate hypothesis features from synthetic data."""
    conj_df = df.copy()
    
    # add new 'category' boolean columns
    # for columns with len(df[col].unique()) <= (len(df))**1/4
    n = len(conj_df) ** 1/4
    
    numeric_cols = conj_df.select_dtypes(include=['number']).columns.tolist()
    boolean_cols = conj_df.select_dtypes(include=['bool']).columns.tolist()

    for col in numeric_cols:
        if len(conj_df[col].unique()) <= n:
            for val in conj_df[col].unique():
                conj_df[f'{col}_is_{val}'] = (conj_df[col] == val).astype(bool)
                boolean_cols += [f'{col}_is_{val}']
    
    return conj_df
