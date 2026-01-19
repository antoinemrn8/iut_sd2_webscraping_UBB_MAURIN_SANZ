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
HEADERS = {
    "User-Agent": "UBB-Stats-StudentProject/1.0 (+contact: your_email@example.com)"
}
TIMEOUT = 20

URL_RESULTS = "https://www.ubbrugby.com/equipes/equipe-premiere/calendrier-resultats.html"

OUTPUT_DIR = Path(r"C:\Users\rafae\OneDrive\Documents\web_scrapping\data")
OUTPUT_FILENAME = "results.csv"

DEBUG = False  # True si tu veux afficher des logs


# =========================
# Regex / parsing
# =========================
WS_RE = re.compile(r"\s+")
WEEKDAYS_FR = r"(Lundi|Mardi|Mercredi|Jeudi|Vendredi|Samedi|Dimanche)"

DATE_RE = re.compile(rf"^{WEEKDAYS_FR}\s+\d{{1,2}}\s+\w+\s+\d{{4}}$", re.IGNORECASE)

SCORE_LINE_RE = re.compile(r"^\s*(\d+)\s*-\s*(\d+)\s+(.*)$")
COMP_RE = re.compile(r"^(Top 14|Champions Cup|Amical Clubs)\b", re.IGNORECASE)

MONTHS_FR = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12
}

DATE_PARTS_RE = re.compile(
    r"^(Lundi|Mardi|Mercredi|Jeudi|Vendredi|Samedi|Dimanche)\s+"
    r"(\d{1,2})\s+([A-Za-zéèêëàâäîïôöùûüç]+)\s+(\d{4})$",
    re.IGNORECASE
)

MONTH_LABEL_RE = re.compile(
    r"^(Janvier|Février|Fevrier|Mars|Avril|Mai|Juin|Juillet|Août|Aout|Septembre|Octobre|Novembre|Décembre|Decembre)\s+20\d{2}$",
    re.IGNORECASE
)

UBB_TOKEN = "Bordeaux-Bègles"

IGNORE_LINES_RE = re.compile(
    r"^(Revivre le match|J'y vais|Acheter mes billets|Billetterie en ligne|Être alerté|Alertes billetterie)$",
    re.IGNORECASE
)


# =========================
# Utils
# =========================
def clean_text(s: str) -> str:
    s = s.replace("\u00a0", " ")
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


def to_date_iso(date_fr: str) -> Optional[str]:
    """
    Utilisé uniquement pour le tri interne, mais on ne l'exporte PAS.
    """
    date_fr = clean_text(date_fr)
    m = DATE_PARTS_RE.match(date_fr)
    if not m:
        return None

    day = int(m.group(2))
    month_name = m.group(3).lower()
    year = int(m.group(4))

    month = MONTHS_FR.get(month_name)
    if not month:
        return None

    return f"{year:04d}-{month:02d}-{day:02d}"


def split_teams_from_rest(rest: str) -> Tuple[Optional[str], Optional[str]]:
    if not rest:
        return None, None

    rest = clean_text(rest).replace("Image", "").strip()
    rest = clean_text(rest)

    if UBB_TOKEN in rest:
        left, right = rest.split(UBB_TOKEN, 1)
        left = left.strip()
        right = right.strip()
        if not left and right:
            return UBB_TOKEN, right
        if left and not right:
            return left, UBB_TOKEN
        if left and right:
            return left, right

    toks = rest.split()
    if len(toks) >= 2:
        mid = len(toks) // 2
        return " ".join(toks[:mid]), " ".join(toks[mid:])
    return rest, None


def find_month_headers(soup: BeautifulSoup) -> List[Tag]:
    headers: List[Tag] = []
    for tag in soup.find_all(["h2", "h3", "h4"]):
        txt = clean_text(tag.get_text(" ", strip=True))
        if MONTH_LABEL_RE.match(txt):
            headers.append(tag)
    return headers


def iter_lines_until_next_month_header(start_header: Tag) -> List[str]:
    lines: List[str] = []

    for el in start_header.next_elements:
        if isinstance(el, Tag) and el is not start_header:
            if el.name in ("h2", "h3", "h4"):
                ht = clean_text(el.get_text(" ", strip=True))
                if MONTH_LABEL_RE.match(ht):
                    break

            txt = clean_text(el.get_text(" ", strip=True))
            if txt and not IGNORE_LINES_RE.match(txt):
                lines.append(txt)

    # dé-doublonnage léger
    dedup = []
    seen = set()
    for l in lines:
        if l not in seen:
            dedup.append(l)
            seen.add(l)
    return dedup


def parse_month_section(lines: List[str], source_url: str) -> List[Dict]:
    """
    ✅ NE RENVOIE PLUS month_section NI date_iso (on les enlève totalement).
    """
    out: List[Dict] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        if DATE_RE.match(line):
            date_str = line

            comp = None
            journee = None

            for j in range(i + 1, min(i + 4, n)):
                comp_line = lines[j]
                if "-" in comp_line:
                    left, right = [p.strip() for p in comp_line.split("-", 1)]
                    if COMP_RE.match(left):
                        comp = left
                        journee = right
                        break
                else:
                    if COMP_RE.match(comp_line):
                        comp = comp_line
                        break

            score_home = score_away = None
            team_home = team_away = None
            score_idx = None

            for j in range(i + 1, min(i + 7, n)):
                m = SCORE_LINE_RE.match(lines[j])
                if m:
                    score_home = int(m.group(1))
                    score_away = int(m.group(2))
                    team_home, team_away = split_teams_from_rest(m.group(3))
                    score_idx = j
                    break

            if score_home is not None and score_away is not None:
                out.append({
                    "date": date_str,
                    "competition": comp,
                    "journee": journee,
                    "team_home": team_home,
                    "team_away": team_away,
                    "score_home": score_home,
                    "score_away": score_away,
                    "source_url": source_url,
                })

            i = (score_idx + 1) if score_idx is not None else (i + 1)
            continue

        i += 1

    return out


def scrape_results(url: str = URL_RESULTS) -> pd.DataFrame:
    session = build_session()
    soup = get_soup(session, url)

    month_headers = find_month_headers(soup)

    if DEBUG:
        print(f"DEBUG: month_headers trouvés = {len(month_headers)}")

    rows: List[Dict] = []
    sort_keys: List[Optional[str]] = []

    for header in month_headers:
        lines = iter_lines_until_next_month_header(header)
        parsed = parse_month_section(lines, url)

        # Tri interne: on calcule un ISO temporaire (non exporté)
        for row in parsed:
            sort_keys.append(to_date_iso(row["date"]))
            rows.append(row)

    df = pd.DataFrame(rows)

    # tri par date (sans colonne date_iso)
    if not df.empty:
        df["_date_iso_tmp"] = [d or "" for d in sort_keys]
        df = df.sort_values(by=["_date_iso_tmp", "competition"], na_position="last").drop(columns=["_date_iso_tmp"])
        df = df.reset_index(drop=True)

    return df


def main():
    df = scrape_results(URL_RESULTS)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / OUTPUT_FILENAME

    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"✅ Export terminé: {out_path} ({len(df)} lignes)")
    print(df.head(10))


if __name__ == "__main__":
    main()
