"""Project configuration / Konfiguracja projektu."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Config:
    """All reproducible analysis settings / Wszystkie ustawienia analizy."""

    base_url: str = "https://api.sejm.gov.pl/sejm"
    terms: tuple[int, ...] = (4, 5, 6, 7, 8, 9, 10)
    valid_votes: tuple[str, ...] = ("YES", "NO", "ABSTAIN")
    min_common_abs: int = 10
    min_common_share: float = 0.60
    near_unanimous_cutoff: float = 0.95
    request_delay: float = 0.03
    max_retries: int = 4
    max_sitting_fallback: int = 150
    data_dir: Path = Path("data")
    force_download: bool = False
    refresh_current_term: bool = False
    force_recompute_metrics: bool = False
    run_contested_robustness: bool = True
    run_proportional_robustness: bool = True
    term_labels: dict[int, str] = field(default_factory=lambda: {
        4: "IV (2001–2005)", 5: "V (2005–2007)",
        6: "VI (2007–2011)", 7: "VII (2011–2015)",
        8: "VIII (2015–2019)", 9: "IX (2019–2023)",
        10: "X (2023–)",
    })

    @property
    def current_term(self) -> int:
        return max(self.terms)

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def sitting_dir(self) -> Path:
        return self.raw_dir / "sittings"

    @property
    def results_dir(self) -> Path:
        return self.data_dir / "results"

    @property
    def param_tag(self) -> str:
        return (f"abs{self.min_common_abs}_share{int(self.min_common_share * 100)}"
                f"_unanim{int(self.near_unanimous_cutoff * 100)}")

    def create_directories(self) -> None:
        """Create output folders / Utwórz katalogi wynikowe."""
        for folder in (self.raw_dir, self.sitting_dir, self.results_dir):
            folder.mkdir(parents=True, exist_ok=True)

