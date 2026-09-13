"""Save exploratory model results / Zapisz wyniki modeli eksploracyjnych."""

import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sejm_network.config import Config
from sejm_network.models import linear_trend, segmented_term_models


def main() -> None:
    cfg = Config()
    path = cfg.results_dir / f"all_terms_main_{cfg.param_tag}.csv"
    results = pd.read_csv(path, parse_dates=["month_date"])
    linear = linear_trend(results)
    segmented = segmented_term_models(results)
    (cfg.results_dir / "linear_trend.txt").write_text(linear.summary().as_text())
    segmented["comparison"].to_csv(cfg.results_dir / "segmented_model_comparison.csv", index=False)
    (cfg.results_dir / "segmented_trend.txt").write_text(segmented["models"]["segmented"].summary().as_text())


if __name__ == "__main__":
    main()

