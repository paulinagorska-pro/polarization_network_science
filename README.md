**Sieci głosowań w Sejmie 2001–2026 / Sejm voting networks 2001–2026**

Polski

Projekt analizuje polaryzację głosowań imiennych w Sejmie RP od IV do X kadencji. Dane są automatycznie pobierane z oficjalnego API Sejmu, zapisywane w lokalnym cache'u i agregowane do miesięcznych sieci podobieństwa.

Węzłem sieci jest poseł. Waga krawędzi między posłami i i j oznacza odsetek wspólnych ważnych głosowań, w których oddali taką samą odpowiedź (YES, NO albo ABSTAIN):

S_ij = liczba zgodnych głosów / liczba wspólnych ważnych głosów

Najważniejsze wyniki:

podobieństwo wewnątrz partii i pomiędzy partiami;

indeks separacji partyjnej: within_similarity - between_similarity;

wariant indeksu z równymi wagami partii i par partii;

modularność formalnego podziału partyjnego;

modularność społeczności wykrytych algorytmem Louvain;

udział głosowań niemal jednomyślnych;

diagnostyka kompletności danych i pokrycia krawędzi.

Pipeline zawiera dwa testy odporności: wyłączenie głosowań, w których ponad 95% ważnych głosów przypada na jedną odpowiedź, oraz proporcjonalny próg wymagający wspólnego udziału pary posłów w co najmniej 60% głosowań w miesiącu (nie mniej niż 10).

Struktura

sejm-voting-network/
├── run_analysis.py                 # uruchomienie całego pipeline'u
├── scripts/
│   ├── analyse_selected_mps.py     # analiza wskazanych posłów
│   └── run_models.py               # trendy liniowe i segmentowe
└── src/sejm_network/
    ├── config.py                   # parametry projektu
    ├── api.py                      # API i cache
    ├── data.py                     # czyszczenie danych
    ├── network.py                  # macierze i grafy
    ├── metrics.py                  # wskaźniki miesięczne
    ├── monthly.py                  # analiza miesięczna
    ├── pipeline.py                 # wszystkie kadencje i robustness checks
    ├── models.py                   # modele trendów
    └── plots.py                    # wykresy

Instalacja i uruchomienie

W katalogu projektu wykonaj:

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_analysis.py

Wybrane opcje:

python run_analysis.py --terms 9 10
python run_analysis.py --refresh-current
python run_analysis.py --skip-robustness
python scripts/run_models.py
python scripts/analyse_selected_mps.py

Surowe dane, wyniki i rysunki są ignorowane przez Git, ponieważ mogą być duże i można je odtworzyć. Pliki źródłowe API mogą zmieniać się w czasie, zwłaszcza w trwającej X kadencji. W analizie porównawczej domyślnie pomijany jest niepełny bieżący miesiąc.

English

This project analyses polarization in Polish Sejm roll-call voting from the 4th through the 10th parliamentary term. It downloads data from the official Sejm API, stores resumable local caches, and constructs monthly voting-similarity networks.

Each node represents an MP. The edge weight between MPs i and j is the proportion of their jointly observed valid votes on which they cast the same response (YES, NO, or ABSTAIN):

S_ij = matching votes / jointly observed valid votes

Core outputs include:

within-party and between-party voting similarity;

party separation: within_similarity - between_similarity;

an equal-party-weight version of the separation index;

modularity of the formal party partition;

modularity of Louvain-detected communities;

the share of near-unanimous votes;

data-coverage and edge-coverage diagnostics.

The pipeline includes two robustness checks: excluding votes where one response accounts for more than 95% of valid votes, and applying a proportional common-vote threshold requiring each MP pair to share at least 60% of the month's votes (and never fewer than 10).

Installation and use

Run from the project directory:

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_analysis.py

Useful variants:

python run_analysis.py --terms 9 10
python run_analysis.py --refresh-current
python run_analysis.py --skip-robustness
python scripts/run_models.py
python scripts/analyse_selected_mps.py

Raw data, derived results, and figures are excluded from Git because they can be large and regenerated. API content may change over time, especially during the ongoing 10th term. The incomplete current month is excluded from comparative analyses by default.

Data source / Źródło danych

Official Sejm API / Oficjalne API Sejmu: https://api.sejm.gov.pl/
