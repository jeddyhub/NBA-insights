
import pandas as pd
import numpy as np

from sklearn.feature_selection import VarianceThreshold
from sklearn.decomposition import PCA
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import pairwise_distances

def analyze_features(X: pd.DataFrame, n_clusters: int = 3) -> pd.DataFrame:

    var_threshold = 0.01
    corr_threshold = 0.9
    random_state = 42

    # 1. Variance threshold
    vt = VarianceThreshold(threshold=var_threshold)
    X_var = vt.fit_transform(X)
    kept_features = X.columns[vt.get_support()]
    X_reduced = pd.DataFrame(X_var, columns=kept_features, index=X.index)

    # 2. Correlation filtering
    corr = X_reduced.corr().abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    to_drop = [col for col in upper.columns if any(upper[col] > corr_threshold)]
    X_reduced = X_reduced.drop(columns=to_drop)

    # 3. Dimensionality reduction
    if n_clusters is None:
        n_clusters = min(20, X_reduced.shape[1] // 2)  # heuristic
        
    dist = pairwise_distances(X_reduced.T, metric="correlation")
    clustering = AgglomerativeClustering(n_clusters=n_clusters,
                                        #  affinity="precomputed",
                                            linkage="average")
    clusters = clustering.fit_predict(dist)
    
    selected_features = []
    for c in np.unique(clusters):
        selected_features.append(np.where(clusters == c)[0][0])  # pick first feature
        
    X_final = X_reduced.iloc[:, selected_features]

    return X_final
