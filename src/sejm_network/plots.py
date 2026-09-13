"""Reusable figures / Funkcje tworzące wykresy."""

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from .models import analysis_sample


def plot_time_series(results: pd.DataFrame, columns: list[str], output: Path, title: str) -> None:
    """Plot monthly indicators / Narysuj miesięczne wskaźniki."""
    df = analysis_sample(results).sort_values("month_date")
    fig, ax = plt.subplots(figsize=(16, 6))
    for column in columns:
        ax.plot(df["month_date"], df[column], label=column)
    ax.set(xlabel="Month / Miesiąc", ylabel="Value / Wartość", title=title)
    if len(columns) > 1: ax.legend()
    fig.tight_layout(); output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=300); plt.close(fig)


def save_standard_figures(results: pd.DataFrame, directory: Path = Path("figures")) -> None:
    """Save the core publication-ready figures / Zapisz podstawowe wykresy."""
    plot_time_series(results, ["polarization"], directory / "polarization.png",
                     "Party separation in Sejm roll-call voting, 2001–2026")
    plot_time_series(results, ["within_similarity", "between_similarity"], directory / "within_between.png",
                     "Within- and between-party voting similarity / Podobieństwo wewnątrz i między partiami")
    plot_time_series(results, ["party_modularity", "louvain_modularity"], directory / "modularity.png",
                     "Voting-network modularity / Modularność sieci głosowań")

