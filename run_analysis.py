"""Command-line entry point / Punkt startowy uruchamiany z terminala."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from sejm_network.config import Config
from sejm_network.pipeline import run_all_terms
from sejm_network.plots import save_standard_figures


def main() -> None:
    parser = argparse.ArgumentParser(description="Sejm voting-network analysis / Analiza sieci głosowań Sejmu")
    parser.add_argument("--terms", nargs="+", type=int, default=list(range(4, 11)))
    parser.add_argument("--refresh-current", action="store_true")
    parser.add_argument("--skip-robustness", action="store_true")
    args = parser.parse_args()
    cfg = Config(terms=tuple(args.terms), refresh_current_term=args.refresh_current,
                 run_contested_robustness=not args.skip_robustness,
                 run_proportional_robustness=not args.skip_robustness)
    outputs = run_all_terms(cfg)
    save_standard_figures(outputs["main"])
    print("Analysis completed / Analiza zakończona")


if __name__ == "__main__":
    main()

