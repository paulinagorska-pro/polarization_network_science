"""Monthly network indicators / Miesięczne wskaźniki sieciowe."""

import networkx as nx
import numpy as np
import pandas as pd
from .network import make_pairs


def calculate_month_metrics(adjacency: pd.DataFrame, mp_info: pd.DataFrame) -> dict:
    """Calculate similarity, polarization and modularity / Policz podobieństwo, polaryzację i modularność."""
    pairs = make_pairs(adjacency, mp_info)
    empty = {"within_similarity": np.nan, "between_similarity": np.nan, "polarization": np.nan,
             "within_similarity_equal_parties": np.nan,
             "between_similarity_equal_party_pairs": np.nan, "polarization_equal_parties": np.nan,
             "party_modularity": np.nan, "louvain_modularity": np.nan, "n_communities": np.nan,
             "n_parties": mp_info["club"].nunique(), "n_pairs": 0}
    if pairs.empty:
        return empty
    within = pairs.loc[pairs["same_party"], "similarity"].mean()
    between = pairs.loc[~pairs["same_party"], "similarity"].mean()
    within_equal = pairs.loc[pairs["same_party"]].groupby("party1")["similarity"].mean().mean()
    between_pairs = pairs.loc[~pairs["same_party"]].copy()
    if between_pairs.empty:
        between_equal = np.nan
    else:
        between_pairs["party_A"] = between_pairs[["party1", "party2"]].min(axis=1)
        between_pairs["party_B"] = between_pairs[["party1", "party2"]].max(axis=1)
        between_equal = between_pairs.groupby(["party_A", "party_B"])["similarity"].mean().mean()

    graph = nx.from_pandas_adjacency(adjacency.fillna(0))
    partition = [set(mp_info.index[mp_info["club"] == party]) for party in mp_info["club"].unique()]
    if graph.number_of_edges() == 0:
        party_q = louvain_q = n_communities = np.nan
    else:
        party_q = nx.community.modularity(graph, partition, weight="weight")
        communities = nx.community.louvain_communities(graph, weight="weight", seed=42)
        louvain_q = nx.community.modularity(graph, communities, weight="weight")
        n_communities = len(communities)
    return {"within_similarity": within, "between_similarity": between,
            "polarization": within - between,
            "within_similarity_equal_parties": within_equal,
            "between_similarity_equal_party_pairs": between_equal,
            "polarization_equal_parties": within_equal - between_equal,
            "party_modularity": party_q, "louvain_modularity": louvain_q,
            "n_communities": n_communities, "n_parties": mp_info["club"].nunique(),
            "n_pairs": len(pairs)}

