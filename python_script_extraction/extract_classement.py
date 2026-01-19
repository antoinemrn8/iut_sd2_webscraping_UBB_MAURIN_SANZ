import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import requests
import pandas as pd
from bs4 import BeautifulSoup, Tag
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# =========================
# CONFIG
# =========================
URL = "https://www.ubbrugby.com/equipes/equipe-premiere/classement.html"

HEADERS = {
    "User-Agent": "UBB-Stats-StudentProject/1.0 (+contact: your_email@example.com)",
    "Accept-Language": "fr-FR,fr;q=0.9",
}
TIMEOUT = 20

OUTPUT_DIR = Path(r"C:\Users\rafae\OneDrive\Documents\web_scrapping\data")
TOP14_FILENAME = "ubb_top14_classement.csv"
CHAMPIONS_CUP_FILENAME = "ubb_champions_cup_classement.csv"

DEBUG = False  # True si tu veux afficher des exemples de lignes parsées


# =========================
# Regex / helpers
# =========================
WS_RE = re.compile(r"\s+")
INT_RE = re.compile(r"^\d+$")
SIGNED_INT_RE = re.compile(r"[+-]?\d+")

HEADER_LINE_RE = re.compile(r"^Pos\s+Équipe\s+Pts\s+MJ", re.IGNORECASE)
VENUE_RE = re.compile(r"^À\s+(domicile|l'extérieur)$", re.IGNORECASE)
POOL_RE = re.compile(r"^Poule\s+(\d+)$", re.IGNORECASE)


def clean_text(s: str) -> str:
    s = s.replace("\u00a0", " ").replace("’", "'")
    s = WS_RE.sub(" ", s)
    return s.strip()


def build_session() -> requests.Session:
    retry = Retry(
        total=5,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.headers.update(HEADERS)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_soup(session: requests.Session, url: str) -> BeautifulSoup:
    r = session.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def dedup_consecutive(lines: List[str]) -> List[str]:
    """✅ Important: on enlève seulement les doublons CONSÉCUTIFS (pas globalement)."""
    out: List[str] = []
    prev: Optional[str] = None
    for l in lines:
        if l != prev:
            out.append(l)
        prev = l
    return out


def iter_lines_until_next_h2(h2: Tag) -> List[str]:
    """
    Récupère le texte après un <h2> jusqu'au prochain <h2>.
    ⚠️ Ne pas dédoublonner globalement, sinon ça casse l'alignement.
    """
    lines: List[str] = []
    for el in h2.next_elements:
        if isinstance(el, Tag) and el is not h2 and el.name == "h2":
            break
        if isinstance(el, Tag):
            txt = clean_text(el.get_text(" ", strip=True))
            if txt:
                lines.append(txt)

    return dedup_consecutive(lines)


def parse_stats_line(line: str) -> Optional[Tuple[int, int, int, int, int, int, int, int, int, int]]:
    """
    Attend exactement 10 nombres :
    Pts, MJ, BO, BD, V, N, D, P, C, Diff
    Exemple: "39 14 5 2 8 0 6 458 363 95"
    """
    nums = [int(x) for x in SIGNED_INT_RE.findall(line)]
    if len(nums) < 10:
        return None
    return tuple(nums[:10])  # type: ignore


def classify_section(section_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    - "Classement" => Top 14
    - "Poule X" => Champions Cup (pool="Poule X")
    """
    s = clean_text(section_name)

    if s.lower() == "classement":
        return "Top 14", None

    if POOL_RE.match(s):
        return "Champions Cup", s

    return None, None


def parse_section(section_name: str, lines: List[str]) -> List[Dict]:
    competition, pool_label = classify_section(section_name)
    if competition is None:
        return []

    if DEBUG:
        print(f"\n--- {competition} | {section_name} ---")
        print(lines[:30])

    out: List[Dict] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # ligne header (Pos Équipe Pts MJ ...)
        if HEADER_LINE_RE.match(line):
            i += 1
            continue

        # une ligne d'équipe commence par le rang (1,2,3,...)
        if INT_RE.match(line):
            rank = int(line)
            i += 1

            # souvent un "Image" juste après
            while i < n and lines[i].lower() == "image":
                i += 1
            if i >= n:
                break

            team = lines[i]
            i += 1

            # stats: on cherche LA prochaine ligne qui a au moins 10 ints
            stats = None
            stats_idx = None
            for j in range(i, min(i + 6, n)):  # fenêtre courte, suffisant ici
                st = parse_stats_line(lines[j])
                if st:
                    stats = st
                    stats_idx = j
                    break

            if stats is None:
                # on ne jette pas d'erreur, on avance
                continue

            # on saute jusqu'après la ligne stats
            i = stats_idx + 1  # type: ignore

            pts, mj, bo, bd, v, n_, d, pts_for, pts_against, diff = stats

            # encore un "Image" parfois
            while i < n and lines[i].lower() == "image":
                i += 1

            # prochain match (ex: "SP Sam. 24 Jan.")
            next_match = None
            if i < n and not VENUE_RE.match(lines[i]) and not INT_RE.match(lines[i]):
                next_match = lines[i]
                i += 1

            # lieu (À domicile / À l'extérieur)
            next_venue = None
            if i < n and VENUE_RE.match(lines[i]):
                next_venue = lines[i]
                i += 1

            out.append({
                "rank": rank,
                "team": team,
                "pts": pts,
                "mj": mj,
                "bo": bo,
                "bd": bd,
                "v": v,
                "n": n_,
                "d": d,
                "pts_for": pts_for,
                "pts_against": pts_against,
                "diff": diff,
                "next_match": next_match,
                "next_venue": next_venue,
                "source_url": URL,
                "competition": competition,
                "pool": pool_label,  # None pour Top14 ; "Poule X" pour CC
            })
            continue

        i += 1

    return out


def scrape_ubb_classements(url: str = URL) -> Tuple[pd.DataFrame, pd.DataFrame]:
    session = build_session()
    soup = get_soup(session, url)

    rows: List[Dict] = []

    for h2 in soup.find_all("h2"):
        section_name = clean_text(h2.get_text(" ", strip=True))
        lines = iter_lines_until_next_h2(h2)
        rows.extend(parse_section(section_name, lines))

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    df_top14 = df[df["competition"] == "Top 14"].copy()
    df_cc = df[df["competition"] == "Champions Cup"].copy()

    # ordre + colonnes propres
    top14_cols = [
        "rank", "team", "pts", "mj", "bo", "bd", "v", "n", "d",
        "pts_for", "pts_against", "diff", "next_match", "next_venue", "source_url"
    ]
    cc_cols = [
        "pool", "rank", "team", "pts", "mj", "bo", "bd", "v", "n", "d",
        "pts_for", "pts_against", "diff", "next_match", "next_venue", "source_url"
    ]

    df_top14 = df_top14[top14_cols].sort_values(by=["rank"]).reset_index(drop=True)
    df_cc = df_cc[cc_cols].sort_values(by=["pool", "rank"]).reset_index(drop=True)

    return df_top14, df_cc


def main():
    df_top14, df_cc = scrape_ubb_classements(URL)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    top14_path = OUTPUT_DIR / TOP14_FILENAME
    cc_path = OUTPUT_DIR / CHAMPIONS_CUP_FILENAME

    df_top14.to_csv(top14_path, index=False, encoding="utf-8-sig")
    df_cc.to_csv(cc_path, index=False, encoding="utf-8-sig")

    print(f"✅ Export Top 14: {top14_path} ({len(df_top14)} lignes)")
    print(f"✅ Export Champions Cup: {cc_path} ({len(df_cc)} lignes)")
    print(df_top14.head(5))
    print(df_cc.head(5))


if __name__ == "__main__":
    main()
