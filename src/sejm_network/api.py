"""Sejm API download and cache / Pobieranie danych z API Sejmu i cache."""

import time
import pandas as pd
import requests

from .config import Config


def get_json(url: str, session: requests.Session, cfg: Config, timeout: int = 60):
    """Download JSON with exponential retries / Pobierz JSON, ponawiając próby."""
    last_error = None
    for attempt in range(1, cfg.max_retries + 1):
        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            last_error = error
            if attempt == cfg.max_retries:
                break
            wait = 2 ** (attempt - 1)
            print(f"Request failed / Błąd zapytania ({attempt}/{cfg.max_retries}); retry in / ponowienie za {wait}s")
            time.sleep(wait)
    raise last_error


def check_terms(cfg: Config) -> pd.DataFrame:
    """Check availability of terms / Sprawdź dostępność kadencji."""
    session, rows = requests.Session(), []
    for term in cfg.terms:
        try:
            info = get_json(f"{cfg.base_url}/term{term}", session, cfg)
            rows.append({"term": term, "label": cfg.term_labels[term], "available": True,
                         "from": info.get("from"), "current": info.get("current")})
        except Exception as error:
            rows.append({"term": term, "label": cfg.term_labels[term], "available": False,
                         "from": None, "current": None, "error": str(error)})
    return pd.DataFrame(rows)


def discover_sittings(term: int, session: requests.Session, cfg: Config) -> list[int]:
    """Find sittings, including the legacy API fallback / Znajdź posiedzenia, także starsze."""
    try:
        proceedings = get_json(f"{cfg.base_url}/term{term}/proceedings", session, cfg)
        sittings = sorted({int(p["number"]) for p in proceedings if p.get("number") and int(p["number"]) > 0})
    except Exception as error:
        print(f"Term / Kadencja {term}: proceedings unavailable / brak listy posiedzeń: {error}")
        sittings = []
    if sittings:
        return sittings

    # Older terms can have votes even when /proceedings is empty.
    # Starsze kadencje mogą mieć głosy mimo pustego /proceedings.
    found = []
    for sitting in range(1, cfg.max_sitting_fallback + 1):
        try:
            votes = get_json(f"{cfg.base_url}/term{term}/votings/{sitting}", session, cfg)
        except requests.HTTPError as error:
            if error.response is not None and error.response.status_code == 404:
                continue
            raise
        if isinstance(votes, list) and votes:
            found.append(sitting)
    if not found:
        raise ValueError(f"No sittings found / Nie znaleziono posiedzeń: term {term}")
    return found


def download_sitting_votes(term: int, sitting: int, session: requests.Session, cfg: Config) -> pd.DataFrame:
    """Download individual votes from one sitting / Pobierz głosy z jednego posiedzenia."""
    votings = get_json(f"{cfg.base_url}/term{term}/votings/{sitting}", session, cfg)
    rows = []
    for voting in votings:
        number = voting["votingNumber"]
        detail = get_json(f"{cfg.base_url}/term{term}/votings/{sitting}/{number}", session, cfg)
        for vote in detail.get("votes", []):
            row = vote.copy()
            row.update({"term": term, "sitting": sitting, "voting_number": number,
                        "date": detail.get("date"), "title": detail.get("title"),
                        "description": detail.get("description"), "topic": detail.get("topic"),
                        "kind": detail.get("kind")})
            rows.append(row)
        time.sleep(cfg.request_delay)
    return pd.DataFrame(rows)


def _valid_cache(df: pd.DataFrame) -> bool:
    required = {"MP", "club", "vote", "term", "sitting", "voting_number", "date"}
    return isinstance(df, pd.DataFrame) and not df.empty and required.issubset(df.columns)


def load_or_download_term(term: int, cfg: Config) -> pd.DataFrame:
    """Load a valid cache or download a whole term / Wczytaj cache lub pobierz kadencję."""
    cfg.create_directories()
    term_cache = cfg.raw_dir / f"sejm_term{term}_votes.pkl"
    refresh = cfg.force_download or (term == cfg.current_term and cfg.refresh_current_term)
    if term_cache.exists() and not refresh:
        cached = pd.read_pickle(term_cache)
        if _valid_cache(cached):
            return cached
        term_cache.unlink()

    session, frames = requests.Session(), []
    sittings = discover_sittings(term, session, cfg)
    for index, sitting in enumerate(sittings, 1):
        cache = cfg.sitting_dir / f"term{term}_sitting{sitting}.pkl"
        if cache.exists() and not refresh:
            frame = pd.read_pickle(cache)
        else:
            print(f"Term / Kadencja {term}, sitting / posiedzenie {sitting} ({index}/{len(sittings)})")
            frame = download_sitting_votes(term, sitting, session, cfg)
            frame.to_pickle(cache)
        if frame.empty:
            frame = download_sitting_votes(term, sitting, session, cfg)
            frame.to_pickle(cache)
        if not frame.empty:
            frames.append(frame)
    if not frames:
        raise ValueError(f"No individual votes / Brak indywidualnych głosów: term {term}")
    result = pd.concat(frames, ignore_index=True)
    if not _valid_cache(result):
        raise ValueError(f"Unexpected API schema / Nieoczekiwany schemat API: term {term}")
    result.to_pickle(term_cache)
    return result

