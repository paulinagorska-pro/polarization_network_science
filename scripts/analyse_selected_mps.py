"""Pairwise similarity for selected MPs / Podobieństwo wybranych posłów."""

import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sejm_network.api import load_or_download_term
from sejm_network.config import Config
from sejm_network.data import prepare_term_data
from sejm_network.network import similarity_and_common

# Edit this list before running / Zmień tę listę przed uruchomieniem.
SELECTED_NAMES = [
    "Krzysztof Gawkowski", "Katarzyna Kotula", "Agnieszka Dziemianowicz-Bąk",
    "Krzysztof Bosak", "Karina Bosak", "Witold Tumanowicz",
]


def main() -> None:
    cfg = Config()
    votes = prepare_term_data(load_or_download_term(10, cfg), 10, cfg)
    votes["full_name"] = votes["firstName"].str.strip() + " " + votes["lastName"].str.strip()
    mapping = votes[votes["full_name"].isin(SELECTED_NAMES)][["MP", "full_name"]].drop_duplicates()
    selected = votes[votes["MP"].isin(mapping["MP"])]
    similarity, common = similarity_and_common(selected, cfg)
    names = mapping.set_index("MP")["full_name"].to_dict()
    similarity, common = similarity.rename(index=names, columns=names), common.rename(index=names, columns=names)
    rows = []
    for i, person_1 in enumerate(similarity.index):
        for person_2 in similarity.index[i + 1:]:
            rows.append({"person_1": person_1, "person_2": person_2,
                         "similarity": similarity.loc[person_1, person_2],
                         "n_common_votes": common.loc[person_1, person_2]})
    output = cfg.results_dir / "selected_mps_similarity.csv"
    pd.DataFrame(rows).sort_values("similarity", ascending=False).to_csv(output, index=False)
    print(f"Saved / Zapisano: {output}")


if __name__ == "__main__":
    main()

