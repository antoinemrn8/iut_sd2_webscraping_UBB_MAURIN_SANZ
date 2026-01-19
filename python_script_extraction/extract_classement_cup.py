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
OUT_FILENAME = "ubb_champions_cup_classement.csv"

# Pour Excel FR : mets ";" (sinon tout part dans une seule colonne)
CSV_SEP = ";"


# =========================
# Helpers
# =========================
WS_RE = re.compile(r"\s+")
VENUE_RE = re.compile(r"^À\s+(domicile|l'extérieur)$", re.IGNORECASE)

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


def parse_next_match_cell(td: Tag) -> Tuple[Optional[str], Optional[str]]:
    lines = [clean_text(x) for x in td.get_text("\n", strip=True).splitlines() if clean_text(x)]
    if not lines:
        return None, None

    next_venue = None
    if VENUE_RE.match(lines[-1]):
        next_venue = lines[-1]
        lines = lines[:-1]

    next_match = " ".join(lines).strip() if lines else None
    return next_match, next_venue


def extract_rows_from_table(table: Tag, pool_label: str) -> List[Dict]:
    """
    Colonnes attendues :
    Pos | Équipe | Pts | MJ | BO | BD | V | N | D | P. | C. | Diff | Prochain match
    """
    rows: List[Dict] = []
    tbody = table.find("tbody")
    if not tbody:
        return rows

    for tr in tbody.find_all("tr", recursive=False):
        tds = tr.find_all("td", recursive=False)
        if len(tds) < 12:
            continue

        # rank
        rank_txt = clean_text(tds[0].get_text(" ", strip=True))
        if not rank_txt.isdigit():
            continue
        rank = int(rank_txt)

        # team (dans div.ranking-table-team)
        team_div = tds[1].find("div", class_="ranking-table-team")
        team = clean_text(team_div.get_text(" ", strip=True)) if team_div else clean_text(tds[1].get_text(" ", strip=True))

        def td_int(i: int) -> Optional[int]:
            txt = clean_text(tds[i].get_text(" ", strip=True))
            return int(txt) if re.fullmatch(r"[+-]?\d+", txt) else None

        pts = td_int(2)
        mj = td_int(3)
        bo = td_int(4)
        bd = td_int(5)
        v = td_int(6)
        n = td_int(7)
        d = td_int(8)
        pts_for = td_int(9)       # P.
        pts_against = td_int(10)  # C.
        diff = td_int(11)

        next_match, next_venue = (None, None)
        if len(tds) >= 13:
            next_match, next_venue = parse_next_match_cell(tds[12])

        rows.append({
            "pool": pool_label,
            "rank": rank,
            "team": team,
            "pts": pts,
            "mj": mj,
            "bo": bo,
            "bd": bd,
            "v": v,
            "n": n,
            "d": d,
            "pts_for": pts_for,
            "pts_against": pts_against,
            "diff": diff,
            "next_match": next_match,
            "next_venue": next_venue,
            "source_url": URL,
        })

    return rows


def scrape_champions_cup() -> pd.DataFrame:
    session = build_session()
    soup = get_soup(session, URL)

    cc_tab = soup.find("div", id="ranking-tab-champions-cup")
    if not cc_tab:
        return pd.DataFrame()

    rows: List[Dict] = []

    # Chaque poule = h2.big-title + div.ranking-table-container + table.ranking-table
    for h2 in cc_tab.find_all("h2", class_="big-title"):
        pool_label = clean_text(h2.get_text(" ", strip=True))  # "Poule 1", ...

        container = h2.find_next_sibling("div", class_="ranking-table-container")
        if not container:
            continue

        table = container.find("table", class_="ranking-table")
        if not table:
            continue

        rows.extend(extract_rows_from_table(table, pool_label))

    df = pd.DataFrame(rows)

    cols = [
        "pool", "rank", "team", "pts", "mj", "bo", "bd", "v", "n", "d",
        "pts_for", "pts_against", "diff", "next_match", "next_venue", "source_url"
    ]
    if not df.empty:
        df = df[cols].sort_values(["pool", "rank"]).reset_index(drop=True)

    return df


def main():
    df = scrape_champions_cup()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / OUT_FILENAME

    df.to_csv(out_path, index=False, encoding="utf-8-sig", sep=CSV_SEP)

    print(f"✅ Export Champions Cup: {out_path} ({len(df)} lignes)")
    print(df.head(10))


if __name__ == "__main__":
    main()
