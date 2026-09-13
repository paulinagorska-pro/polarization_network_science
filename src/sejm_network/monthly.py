"""Monthly analysis orchestration / Sterowanie analizą miesięczną."""

import numpy as np
import pandas as pd
from .config import Config
from .metrics import calculate_month_metrics
from .network import apply_min_common, make_mp_info, similarity_and_common


def run_monthly_analysis(df: pd.DataFrame, term: int, cfg: Config,
                         threshold_mode: str = "fixed") -> pd.DataFrame:
    """Build and summarize one network per month / Zbuduj i opisz jedną sieć na miesiąc."""
    months = pd.period_range(df["month"].min(), df["month"].max(), freq="M").astype(str)
    results = []
    for month in months:
        current = df[df["month"] == month]
        n_votings, n_mps = current["vote_id"].nunique(), current["MP"].nunique()
        if threshold_mode == "fixed":
            minimum = cfg.min_common_abs
        elif threshold_mode == "proportional":
            minimum = max(cfg.min_common_abs, int(np.ceil(n_votings * cfg.min_common_share)))
        else:
            raise ValueError("threshold_mode must be / musi być: fixed or / albo proportional")
        base = {"term": term, "month": month, "n_votings": n_votings,
                "n_active_mps": n_mps, "min_common_used": minimum}
        if n_votings < cfg.min_common_abs:
            base.update({key: np.nan for key in ("within_similarity", "between_similarity", "polarization",
                "within_similarity_equal_parties", "between_similarity_equal_party_pairs",
                "polarization_equal_parties", "party_modularity", "louvain_modularity",
                "n_communities", "n_parties", "median_common_votes", "edge_coverage",
                "share_near_unanimous")})
            base.update({"n_pairs": 0, "n_mps_multiple_clubs": 0, "status": "too_few_votings"})
            results.append(base)
            continue
        similarity, common = similarity_and_common(current, cfg)
        adjacency = apply_min_common(similarity, common, minimum)
        info = make_mp_info(current, adjacency)
        metrics = calculate_month_metrics(adjacency, info)
        upper = np.triu_indices_from(common, k=1)
        common_values, adjacency_values = common.to_numpy()[upper], adjacency.to_numpy()[upper]
        unique_votes = current[["vote_id", "dominant_share"]].drop_duplicates("vote_id")
        metrics.update(base)
        metrics.update({"median_common_votes": np.median(common_values),
                        "edge_coverage": np.isfinite(adjacency_values).mean(),
                        "n_mps_multiple_clubs": int((info["club_nunique"] > 1).sum()),
                        "share_near_unanimous": (unique_votes["dominant_share"] > cfg.near_unanimous_cutoff).mean(),
                        "status": "ok"})
        results.append(metrics)
    result = pd.DataFrame(results)
    result["month_date"] = pd.to_datetime(result["month"])
    result["term_label"] = result["term"].map(cfg.term_labels)
    result["is_partial_current_month"] = pd.PeriodIndex(result["month"], freq="M") == pd.Timestamp.today().to_period("M")
    return result

