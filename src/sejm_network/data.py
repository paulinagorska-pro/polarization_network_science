"""Data preparation and diagnostics / Przygotowanie i diagnostyka danych."""

import pandas as pd
from .config import Config

REQUIRED_COLUMNS = {"MP", "club", "firstName", "lastName", "vote", "term", "sitting", "voting_number", "date"}


def prepare_term_data(term_df: pd.DataFrame, term: int, cfg: Config) -> pd.DataFrame:
    """Prepare one term for monthly analysis / Przygotuj kadencję do analiz miesięcznych."""
    if term_df.empty:
        raise ValueError(f"Empty term / Pusta kadencja: {term}")
    missing = REQUIRED_COLUMNS - set(term_df.columns)
    if missing:
        raise ValueError(f"Missing columns / Brak kolumn: {sorted(missing)}")
    df = term_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["vote_id"] = (df["term"].astype(str) + "_" + df["sitting"].astype(str)
                     + "_" + df["voting_number"].astype(str))
    df["month"] = df["date"].dt.to_period("M").astype(str)
    regular = df[df["vote"].isin(cfg.valid_votes)].copy()
    if regular.empty:
        raise ValueError(f"No YES/NO/ABSTAIN votes / Brak regularnych głosów: term {term}")
    dominant = (regular.groupby("vote_id")["vote"].value_counts(normalize=True)
                .groupby(level=0).max())
    regular["dominant_share"] = regular["vote_id"].map(dominant)
    return regular


def term_diagnostics(regular: pd.DataFrame, term: int, cfg: Config) -> dict:
    """Return term-level quality indicators / Zwróć diagnostykę kadencji."""
    votes = regular[["vote_id", "month", "dominant_share"]].drop_duplicates("vote_id")
    return {"term": term, "label": cfg.term_labels[term], "date_min": regular["date"].min(),
            "date_max": regular["date"].max(), "n_vote_records": len(regular),
            "n_votings": regular["vote_id"].nunique(), "n_mps": regular["MP"].nunique(),
            "n_clubs": regular["club"].nunique(dropna=True),
            "n_months_with_votings": regular["month"].nunique(),
            "share_near_unanimous": (votes["dominant_share"] > cfg.near_unanimous_cutoff).mean()}

