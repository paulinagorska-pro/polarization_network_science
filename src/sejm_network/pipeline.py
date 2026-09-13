"""End-to-end processing pipeline / Kompletny pipeline przetwarzania."""

import gc
import pandas as pd
from .api import check_terms, load_or_download_term
from .config import Config
from .data import prepare_term_data
from .monthly import run_monthly_analysis


def term_diagnostics(df: pd.DataFrame, term: int, cfg: Config) -> dict:
    """Summarize coverage and quality / Podsumuj kompletność i jakość danych."""
    votes = df[["vote_id", "month", "dominant_share"]].drop_duplicates("vote_id")
    return {"term": term, "label": cfg.term_labels[term], "date_min": df["date"].min(),
            "date_max": df["date"].max(), "n_vote_records": len(df),
            "n_votings": df["vote_id"].nunique(), "n_mps": df["MP"].nunique(),
            "n_clubs": df["club"].nunique(dropna=True), "n_months_with_votings": df["month"].nunique(),
            "share_near_unanimous": (votes["dominant_share"] > cfg.near_unanimous_cutoff).mean()}


def process_term(term: int, cfg: Config) -> tuple[pd.DataFrame, pd.DataFrame | None, pd.DataFrame | None, dict]:
    """Process and cache all variants for one term / Przetwórz i zapisz warianty jednej kadencji."""
    cfg.create_directories()
    files = {name: cfg.results_dir / f"term{term}_monthly_{name}_{cfg.param_tag}.csv"
             for name in ("main", "contested", "proportional")}
    diagnostics_file = cfg.results_dir / f"term{term}_diagnostics_{cfg.param_tag}.csv"
    recompute = cfg.force_recompute_metrics or not files["main"].exists()
    need_raw = recompute or not diagnostics_file.exists() or cfg.run_contested_robustness or cfg.run_proportional_robustness
    regular = prepare_term_data(load_or_download_term(term, cfg), term, cfg) if need_raw else None
    if regular is not None:
        diagnostics = term_diagnostics(regular, term, cfg)
        pd.DataFrame([diagnostics]).to_csv(diagnostics_file, index=False)
    else:
        diagnostics = pd.read_csv(diagnostics_file).iloc[0].to_dict()

    def calculate_or_load(name: str, data: pd.DataFrame, mode: str) -> pd.DataFrame:
        if cfg.force_recompute_metrics or not files[name].exists():
            result = run_monthly_analysis(data, term, cfg, mode)
            result.to_csv(files[name], index=False)
            return result
        return pd.read_csv(files[name], parse_dates=["month_date"])

    main = calculate_or_load("main", regular, "fixed") if recompute else pd.read_csv(files["main"], parse_dates=["month_date"])
    contested = None
    if cfg.run_contested_robustness:
        contested = calculate_or_load("contested", regular[regular["dominant_share"] <= cfg.near_unanimous_cutoff], "fixed")
    proportional = None
    if cfg.run_proportional_robustness:
        proportional = calculate_or_load("proportional", regular, "proportional")
    del regular
    gc.collect()
    return main, contested, proportional, diagnostics


def run_all_terms(cfg: Config) -> dict[str, pd.DataFrame]:
    """Run all terms and save combined tables / Uruchom wszystkie kadencje i zapisz tabele zbiorcze."""
    cfg.create_directories()
    availability = check_terms(cfg)
    availability.to_csv(cfg.results_dir / "term_availability.csv", index=False)
    main, contested, proportional, diagnostics = [], [], [], []
    for term in cfg.terms:
        a, b, c, d = process_term(term, cfg)
        main.append(a); diagnostics.append(d)
        if b is not None: contested.append(b)
        if c is not None: proportional.append(c)
    outputs = {"main": pd.concat(main, ignore_index=True), "diagnostics": pd.DataFrame(diagnostics)}
    if contested: outputs["contested"] = pd.concat(contested, ignore_index=True)
    if proportional: outputs["proportional"] = pd.concat(proportional, ignore_index=True)
    for name, frame in outputs.items():
        frame.to_csv(cfg.results_dir / f"all_terms_{name}_{cfg.param_tag}.csv", index=False)
    return outputs

