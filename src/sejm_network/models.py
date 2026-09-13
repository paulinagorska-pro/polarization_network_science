"""Exploratory time-trend models / Eksploracyjne modele trendów czasowych."""

import numpy as np
import pandas as pd
import statsmodels.api as sm


def analysis_sample(results: pd.DataFrame) -> pd.DataFrame:
    """Exclude failed and partial months / Usuń miesiące błędne i niepełne."""
    return results[(results["status"] == "ok") & ~results["is_partial_current_month"].fillna(False)].copy()


def linear_trend(results: pd.DataFrame, outcome: str = "polarization", hac_lags: int = 3):
    """Fit OLS time trend with HAC errors / Dopasuj trend OLS z błędami HAC."""
    df = analysis_sample(results).dropna(subset=[outcome, "month_date"]).sort_values("month_date")
    df["time_years"] = (df["month_date"] - df["month_date"].min()).dt.days / 365.25
    return sm.OLS(df[outcome], sm.add_constant(df[["time_years"]])).fit(cov_type="HAC", cov_kwds={"maxlags": hac_lags})


def segmented_term_models(results: pd.DataFrame, hac_lags: int = 3) -> dict:
    """Compare linear, level-shift and segmented trends / Porównaj trend liniowy i modele segmentowe."""
    df = analysis_sample(results).dropna(subset=["polarization", "month_date", "term"]).sort_values("month_date")
    start = df["month_date"].min()
    df["time_years"] = (df["month_date"] - start).dt.days / 365.25
    starts = df.groupby("term")["month_date"].min().sort_index()
    break_terms = [int(x) for x in starts.index[1:]]
    for term in break_terms:
        break_time = (starts.loc[term] - start).days / 365.25
        df[f"post_term_{term}"] = (df["month_date"] >= starts.loc[term]).astype(int)
        df[f"after_term_{term}"] = np.maximum(0, df["time_years"] - break_time)
    post = [f"post_term_{x}" for x in break_terms]
    after = [f"after_term_{x}" for x in break_terms]
    fit = lambda cols: sm.OLS(df["polarization"], sm.add_constant(df[cols])).fit(
        cov_type="HAC", cov_kwds={"maxlags": hac_lags})
    models = {"linear": fit(["time_years"]), "level": fit(["time_years"] + post),
              "segmented": fit(["time_years"] + post + after)}
    comparison = pd.DataFrame([{"model": name, "aic": model.aic, "bic": model.bic,
                                "adjusted_r2": model.rsquared_adj} for name, model in models.items()])
    return {"data": df, "models": models, "comparison": comparison, "break_terms": break_terms}

