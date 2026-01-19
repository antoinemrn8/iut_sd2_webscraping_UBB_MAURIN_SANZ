import re
import time
from pathlib import Path
from typing import Optional, Dict, List
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# =========================
# CONFIG
# =========================
HEADERS = {
    "User-Agent": "UBB-Stats-StudentProject/1.0 (+contact: your_email@example.com)",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

TIMEOUT = 20
SLEEP_SECONDS = 1.0  # politesse serveur

# Page "générique" effectif (on récupère toutes les URLs joueurs ici)
ROSTER_URL = "https://www.ubbrugby.com/equipes/equipe-premiere/effectif.html"

# Dossier de sortie
OUTPUT_DIR = Path(r"C:\Users\rafae\OneDrive\Documents\web_scrapping\data")
OUTPUT_FILENAME = "players.csv"


# =========================
# HELPERS
# =========================
ID_RE = re.compile(r"/(j\d+)-", re.IGNORECASE)
YEAR_RE = re.compile(r"(\d{4})")
INT_RE = re.compile(r"(\d+)")


def clean_text(s: str) -> str:
    return s.replace("\u00a0", " ").strip()


def parse_int(s: Optional[str]) -> Optional[int]:
    if not s:
        return None
    m = INT_RE.search(clean_text(s))
    return int(m.group(1)) if m else None


def extract_player_id(url: str) -> Optional[str]:
    m = ID_RE.search(url)
    return m.group(1) if m else None


def build_session() -> requests.Session:
    """
    Session + retries (pratique si le site renvoie parfois 429/5xx).
    """
    session = requests.Session()
    session.headers.update(HEADERS)

    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_soup(session: requests.Session, url: str) -> BeautifulSoup:
    r = session.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def collect_player_urls(session: requests.Session, roster_url: str) -> List[str]:
    """
    Récupère automatiquement toutes les URLs joueurs depuis la page effectif.
    On filtre les fiches joueurs: /effectif/j123-...
    """
    soup = get_soup(session, roster_url)

    pattern = re.compile(r"/equipes/equipe-premiere/effectif/j\d+-", re.IGNORECASE)
    urls = set()

    for a in soup.select("a[href]"):
        href = a.get("href", "")
        if pattern.search(href):
            urls.add(urljoin(roster_url, href))

    def sort_key(u: str) -> int:
        pid = extract_player_id(u)
        return int(pid[1:]) if pid else 10**9

    return sorted(urls, key=sort_key)


def parse_dt_dd_block(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Lit le bloc "Infos clés" (dl/dt/dd) -> dictionnaire.
    Ex: Taille -> 182 cm ; Poids -> 148 kg ; Âge -> 34 ans ; Nationalité -> ...
    """
    out: Dict[str, str] = {}
    dl = soup.select_one(".player-detail-info-list dl")
    if not dl:
        return out

    for div in dl.select("div"):
        dt = div.find("dt")
        dd = div.find("dd")
        if dt and dd:
            key = clean_text(dt.get_text(" ", strip=True))
            val = clean_text(dd.get_text(" ", strip=True))
            if key:
                out[key] = val
    return out


def parse_global_stats(soup: BeautifulSoup) -> Dict[str, Optional[int]]:
    """
    Bloc 'Depuis 20xx' + stats globales (sélections, matchs, essais, points).
    """
    out = {"since_year": None, "caps": None, "matches": None, "tries": None, "points": None}

    # Depuis YYYY
    h2 = soup.select_one(".player-global-stats-header h2")
    if h2:
        m = YEAR_RE.search(clean_text(h2.get_text(" ", strip=True)))
        if m:
            out["since_year"] = int(m.group(1))

    # Liste stats (valeur + libellé)
    for item in soup.select(".player-global-stats-list .player-detail-stat"):
        val_el = item.select_one(".player-detail-stat-value")
        txt_el = item.select_one(".player-detail-stat-text")
        val = parse_int(val_el.get_text(" ", strip=True)) if val_el else None
        label = clean_text(txt_el.get_text(" ", strip=True)).lower() if txt_el else ""

        if val is None or not label:
            continue

        # Mapping libellés -> colonnes
        if "sélection" in label:
            out["caps"] = val
        elif "match" in label:
            out["matches"] = val
        elif "essai" in label:
            out["tries"] = val
        elif label == "points" or "point" in label:
            out["points"] = val

    return out


def parse_name_and_position(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    """
    Nom: spans firstname/lastname si présents, sinon fallback h1.
    Poste: tags dans .player-detail-metadata (souvent: [ligne] puis [poste]).
    """
    # Name
    fn = soup.select_one(".player-detail-firstname")
    ln = soup.select_one(".player-detail-lastname")
    if fn and ln:
        name = f"{clean_text(fn.get_text())} {clean_text(ln.get_text())}"
    else:
        h1 = soup.find("h1")
        name = clean_text(h1.get_text(" ", strip=True)) if h1 else None

    # Position (2e tag souvent)
    tags = [clean_text(t.get_text(" ", strip=True)) for t in soup.select(".player-detail-metadata .tag")]
    position = None
    if len(tags) >= 2:
        position = tags[1]  # ex: "Pilier"
    elif len(tags) == 1:
        position = tags[0]

    return {"name": name, "position": position}


def scrape_one_player(session: requests.Session, url: str) -> Dict:
    soup = get_soup(session, url)

    player_id = extract_player_id(url)
    meta = parse_name_and_position(soup)

    info = parse_dt_dd_block(soup)
    stats = parse_global_stats(soup)

    return {
        "player_id": player_id,
        "name": meta.get("name"),
        "position": meta.get("position"),
        "height_cm": parse_int(info.get("Taille")),
        "weight_kg": parse_int(info.get("Poids")),
        "age": parse_int(info.get("Âge")),
        "nationality": info.get("Nationalité"),
        **stats,
        "url": url,
    }


def main():
    session = build_session()

    player_urls = collect_player_urls(session, ROSTER_URL)
    print(f"✅ {len(player_urls)} joueurs détectés depuis {ROSTER_URL}")

    rows: List[Dict] = []
    for i, url in enumerate(player_urls, start=1):
        try:
            print(f"[{i}/{len(player_urls)}] {url}")
            rows.append(scrape_one_player(session, url))
        except Exception as e:
            rows.append({
                "player_id": extract_player_id(url),
                "url": url,
                "error": str(e),
            })
        time.sleep(SLEEP_SECONDS)

    df = pd.DataFrame(rows)

    # Ordre propre des colonnes (sans macro_group / line_group_raw / position_text)
    cols_order = [
        "player_id", "name", "position",
        "height_cm", "weight_kg", "age", "nationality",
        "since_year", "caps", "matches", "tries", "points",
        "url", "error"
    ]
    df = df[[c for c in cols_order if c in df.columns] + [c for c in df.columns if c not in cols_order]]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / OUTPUT_FILENAME

    # utf-8-sig = Excel Windows lit mieux les accents
    df.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"\n✅ Export terminé : {out_path} ({len(df)} lignes)")
    print(df.head(5))


if __name__ == "__main__":
    main()
