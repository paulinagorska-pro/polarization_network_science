"""Voting-similarity network construction / Budowa sieci podobieństwa głosowań."""

import networkx as nx
import numpy as np
import pandas as pd

from .config import Config


def similarity_and_common(df: pd.DataFrame, cfg: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate similarity and common-vote matrices / Policz podobieństwo i wspólne głosy."""
    df = df[df["vote"].isin(cfg.valid_votes)]
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    matrix = df.pivot_table(index="MP", columns="vote_id", values="vote", aggfunc="first")
    participated = matrix.isin(cfg.valid_votes).astype(int)
    common = participated @ participated.T
    same = np.zeros((len(matrix), len(matrix)), dtype=float)
    for vote_type in cfg.valid_votes:
        indicator = (matrix == vote_type).astype(int)
        same += (indicator @ indicator.T).to_numpy()
    common_array = common.to_numpy(dtype=float)
    similarity_array = np.full(common_array.shape, np.nan)
    np.divide(same, common_array, out=similarity_array, where=common_array > 0)
    np.fill_diagonal(similarity_array, 0)
    similarity = pd.DataFrame(similarity_array, index=matrix.index, columns=matrix.index)
    return similarity, common


def apply_min_common(similarity: pd.DataFrame, common: pd.DataFrame, minimum: int) -> pd.DataFrame:
    """Remove insufficiently supported edges / Usuń krawędzie o zbyt małym wsparciu."""
    adjacency = similarity.mask(common < minimum)
    values = adjacency.to_numpy(copy=True)
    np.fill_diagonal(values, 0)
    return pd.DataFrame(values, index=adjacency.index, columns=adjacency.columns)


def _modal_value(series: pd.Series):
    values = series.dropna()
    modes = values.mode()
    return "Unknown" if values.empty else (values.iloc[-1] if modes.empty else modes.iloc[0])


def make_mp_info(df: pd.DataFrame, adjacency: pd.DataFrame | None = None) -> pd.DataFrame:
    """Create monthly MP metadata / Utwórz miesięczne metadane posłów."""
    info = (df.sort_values("date").groupby("MP")
            .agg(firstName=("firstName", "last"), lastName=("lastName", "last"),
                 club=("club", _modal_value), club_nunique=("club", lambda x: x.nunique(dropna=True))))
    info["club"] = info["club"].fillna("Unknown")
    info["name"] = (info["firstName"].fillna("") + " " + info["lastName"].fillna("")).str.strip()
    return info.loc[adjacency.index] if adjacency is not None else info


def make_pairs(adjacency: pd.DataFrame, mp_info: pd.DataFrame) -> pd.DataFrame:
    """Convert upper triangle into an MP-pair table / Zamień macierz na tabelę par posłów."""
    rows, cols = np.triu_indices_from(adjacency, k=1)
    pairs = pd.DataFrame({"MP1": adjacency.index[rows], "MP2": adjacency.columns[cols],
                          "similarity": adjacency.to_numpy()[rows, cols]}).dropna(subset=["similarity"])
    pairs["party1"] = pairs["MP1"].map(mp_info["club"])
    pairs["party2"] = pairs["MP2"].map(mp_info["club"])
    pairs["same_party"] = pairs["party1"] == pairs["party2"]
    return pairs


def make_knn_graph(adjacency: pd.DataFrame, mp_info: pd.DataFrame, k: int = 5) -> nx.Graph:
    """Build a sparse graph for plotting only / Zbuduj rzadki graf wyłącznie do wizualizacji."""
    graph = nx.Graph()
    for mp in adjacency.index:
        graph.add_node(mp, name=mp_info.loc[mp, "name"], club=mp_info.loc[mp, "club"])
    for mp in adjacency.index:
        for other, value in adjacency.loc[mp].drop(index=mp).dropna().nlargest(k).items():
            graph.add_edge(mp, other, weight=value)
    return graph

