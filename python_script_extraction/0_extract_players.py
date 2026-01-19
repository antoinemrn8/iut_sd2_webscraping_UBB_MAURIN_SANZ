import re
import time
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from urllib.parse import urljoin

import requests
import pandas as pd
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "UBB-Stats-StudentProject/1.0 (+contact: your_email@example.com)"
}

TIMEOUT = 20
SLEEP_SECONDS = 1.0  # politesse serveur

# ✅ URL "générique" : on récupère tous les joueurs depuis cette page
ROSTER_URL = "https://www.ubbrugby.com/equipes/equipe-premiere/effectif.html"  # :contentReference[oaicite:1]{index=1}

# ✅ dossier de sortie demandé
OUTPUT_DIR = Path(r"C:\Users\rafae\OneDrive\Documents\web_scrapping\data")
OUTPUT_FILENAME = "players.csv"


# ---- Helpers parsing ----
def extract_player_id(url: str) -> Optional[str]:
    m = re.search(r"/(j\d+)-", url)
    return m.group(1) if m else None


def clean_nbsp(s: str) -> str:
    return s.replace("\u00a0", " ").strip()


def parse_int_from_text(s: Optional[str]) -> Optional[int]:
    if not s:
        return None
    s = clean_nbsp(s)
    m = re.search(r"(\d+)", s)
    return int(m.group(1)) if m else None


def find_value_after_label(soup: BeautifulSoup, label: str) -> Optional[str]:
    node = soup.find(string=lambda x: isinstance(x, str) and clean_nbsp(x) == label)
    if not node:
        return None

    for el in node.parent.next_elements:
        if isinstance(el, str):
            txt = clean_nbsp(el)
            if txt and txt != label:
                return txt
    return None


def extract_group_and_position(soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Exemples rencontrés sur les pages UBB :
      - "1ère ligne Pilier"
      - "2ème ligne"
      - "Charnière Ouvreur"
      - "Aile Ailier"
      - "Centre Centre"
      - "Arrière Arrière"
    """
    h1 = soup.find("h1")
    if not h1:
        return None, None, None

    candidates = []
    for el in h1.next_elements:
        if isinstance(el, str):
            t = clean_nbsp(el)
            if t:
                candidates.append(t)
        if len(candidates) >= 30:
            break

    keywords = ["ligne", "pilier", "talonneur", "centre", "aile", "ailier", "arrière", "charnière", "demi", "ouvreur"]
    for t in candidates:
        tl = t.lower()
        if any(k in tl for k in keywords):
            # 1) cas "... ligne ..."
            m = re.match(r"^(.*?ligne)\s+(.*)$", t, flags=re.IGNORECASE)
            if m:
                return t, m.group(1).strip(), m.group(2).strip()

            # 2) cas Charnière/Centre/Aile/Arrière + poste
            m = re.match(r"^(Charnière|Centre|Aile|Arrière)\s+(.*)$", t, flags=re.IGNORECASE)
            if m:
                return t, m.group(1).strip(), m.group(2).strip()

            # 3) fallback : on garde tout en brut
            return t, None, t

    return None, None, None


def normalize_macro_group(line_group_raw: Optional[str], position: Optional[str], position_text: Optional[str]) -> Optional[str]:
    """
    Objectif : obtenir tes groupes : 1ère Ligne / 2ème ligne / 3ème ligne / Charnière / Centre / Ailes / Arrière
    """
    src = (line_group_raw or position_text or "").lower()

    if "1ère ligne" in src or "1ere ligne" in src:
        return "1ère Ligne"
    if "2ème ligne" in src or "2eme ligne" in src:
        return "2ème ligne"
    if "3ème ligne" in src or "3eme ligne" in src:
        return "3ème ligne"
    if "charnière" in src or "charniere" in src:
        return "Charnière"
    if "centre" in src:
        return "Centre"
    if "aile" in src or (position and "ailier" in position.lower()):
        return "Ailes"
    if "arrière" in src or "arriere" in src:
        return "Arrière"

    return None


def extract_since_block_stats(soup: BeautifulSoup) -> Dict[str, Optional[int]]:
    text = soup.get_text("\n", strip=True)
    out = {"since_year": None, "caps": None, "matches": None, "tries": None, "points": None}

    m_year = re.search(r"Depuis\s+(\d{4})", text)
    if m_year:
        out["since_year"] = int(m_year.group(1))

    m_caps = re.search(r"(\d+)\s+sélections nationales", text)
    if m_caps:
        out["caps"] = int(m_caps.group(1))

    m_matches = re.search(r"(\d+)\s+matchs joués", text)
    if m_matches:
        out["matches"] = int(m_matches.group(1))

    m_tries = re.search(r"(\d+)\s+essais", text)
    if m_tries:
        out["tries"] = int(m_tries.group(1))

    m_points = re.search(r"(\d+)\s+points", text)
    if m_points:
        out["points"] = int(m_points.group(1))

    return out


def collect_player_urls(session: requests.Session, roster_url: str) -> List[str]:
    """
    Récupère automatiquement toutes les URLs joueurs depuis la page effectif.
    Filtre uniquement les fiches joueurs (préfixe j...), pas le staff (préfixe s...). :contentReference[oaicite:2]{index=2}
    """
    r = session.get(roster_url, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

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


def scrape_one_player(session: requests.Session, url: str) -> Dict:
    r = session.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    player_id = extract_player_id(url)
    name = soup.find("h1").get_text(strip=True) if soup.find("h1") else None

    pos_text, line_group_raw, position = extract_group_and_position(soup)
    macro_group = normalize_macro_group(line_group_raw, position, pos_text)

    height = find_value_after_label(soup, "Taille")
    weight = find_value_after_label(soup, "Poids")
    age = find_value_after_label(soup, "Âge")
    nationality = find_value_after_label(soup, "Nationalité")

    since_stats = extract_since_block_stats(soup)

    return {
        "player_id": player_id,
        "name": name,
        "macro_group": macro_group,
        "position_text": pos_text,
        "line_group_raw": line_group_raw,
        "position": position,
        "height_cm": parse_int_from_text(height),
        "weight_kg": parse_int_from_text(weight),
        "age": parse_int_from_text(age),
        "nationality": nationality,
        **since_stats,
        "url": url,
    }


def main():
    session = requests.Session()
    session.headers.update(HEADERS)

    # 1) URLs auto
    player_urls = collect_player_urls(session, ROSTER_URL)
    print(f"✅ {len(player_urls)} joueurs détectés depuis {ROSTER_URL}")

    # 2) scrape
    rows = []
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

    cols_order = [
        "player_id", "name", "position",
        "height_cm", "weight_kg", "age", "nationality",
        "since_year", "caps", "matches", "tries", "points",
        "url", "error"
    ]
    df = df[[c for c in cols_order if c in df.columns] + [c for c in df.columns if c not in cols_order]]

    # 3) export dans le dossier demandé
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / OUTPUT_FILENAME

    # utf-8-sig -> Excel Windows ouvre mieux les accents
    df.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"\n✅ Export terminé : {out_path}")
    print(df.head(5))


if __name__ == "__main__":
    main()