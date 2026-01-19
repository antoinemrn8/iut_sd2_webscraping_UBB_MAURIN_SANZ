import os
import re
import time
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

# -----------------------
# CONFIG
# -----------------------
HEADERS = {"User-Agent": "UBB-Scraper/1.0 (+student project)"}
TIMEOUT = 20
SLEEP_SECONDS = 0.8

URL_EFFECTIF = "https://www.ubbrugby.com/equipes/equipe-premiere/effectif.html"

OUTPUT_DIR = r"C:\Users\rafae\OneDrive\Documents\web_scrapping\data"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "ubb_players_id_name_image.csv")

PLAYER_URL_RE = re.compile(r"/effectif/(j\d+)-", re.IGNORECASE)  # ex: /effectif/j286-benjamin-tameifuna.html


# -----------------------
# HELPERS
# -----------------------
def fetch_soup(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def extract_player_id(player_url: str) -> str | None:
    m = PLAYER_URL_RE.search(player_url)
    return m.group(1) if m else None


def collect_player_urls(effectif_url: str) -> list[str]:
    soup = fetch_soup(effectif_url)
    urls = set()

    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        if not href:
            continue
        full = urljoin(effectif_url, href)

        # On garde uniquement les pages joueur (pattern /effectif/jXXX-...)
        if PLAYER_URL_RE.search(full) and full.endswith(".html"):
            urls.add(full)

    return sorted(urls)


def extract_first_last_name(soup: BeautifulSoup) -> tuple[str | None, str | None, str | None]:
    """
    Renvoie (full_name, firstname, lastname)
    Essaie d'abord des spans dédiés, sinon fallback sur h1.
    """
    # Cas le plus propre si le site a des spans dédiés
    fn = soup.select_one(".player-detail-firstname")
    ln = soup.select_one(".player-detail-lastname")
    if fn and ln:
        firstname = fn.get_text(strip=True)
        lastname = ln.get_text(strip=True)
        full = f"{firstname} {lastname}".strip()
        return full, firstname, lastname

    # Fallback sur h1
    h1 = soup.find("h1")
    if not h1:
        return None, None, None

    full = h1.get_text(" ", strip=True)
    # Heuristique simple : dernier mot en MAJ = nom
    parts = full.split()
    if len(parts) >= 2 and parts[-1].isupper():
        firstname = " ".join(parts[:-1])
        lastname = parts[-1]
        return full, firstname, lastname

    return full, None, None


def extract_profile_image_url(soup: BeautifulSoup) -> str | None:
    """
    On cherche l'image principale du joueur.
    Stratégie robuste : prendre le premier <img> dont l'alt commence par 'Photo de'
    et récupérer en priorité:
      - srcset (on prend la dernière URL => souvent la meilleure)
      - sinon src
    """
    img = soup.find("img", attrs={"alt": re.compile(r"^\s*Photo de", re.IGNORECASE)})
    if not img:
        return None

    srcset = (img.get("srcset") or "").strip()
    if srcset:
        # srcset = "url1 1x, url2 2x" -> on prend la dernière url
        last_part = srcset.split(",")[-1].strip()
        url = last_part.split()[0].strip()
        return url

    src = (img.get("src") or "").strip()
    return src or None


def scrape_one_player(player_url: str) -> dict:
    soup = fetch_soup(player_url)

    player_id = extract_player_id(player_url)
    full_name, firstname, lastname = extract_first_last_name(soup)
    image_url = extract_profile_image_url(soup)

    return {
        "player_id": player_id,
        "firstname": firstname,
        "lastname": lastname,
        "full_name": full_name,
        "image_url": image_url,
        "player_url": player_url,
    }


# -----------------------
# MAIN
# -----------------------
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    player_urls = collect_player_urls(URL_EFFECTIF)
    print(f"✅ {len(player_urls)} pages joueurs trouvées")

    rows = []
    for i, url in enumerate(player_urls, start=1):
        try:
            print(f"[{i}/{len(player_urls)}] {url}")
            rows.append(scrape_one_player(url))
        except Exception as e:
            rows.append({
                "player_id": extract_player_id(url),
                "firstname": None,
                "lastname": None,
                "full_name": None,
                "image_url": None,
                "player_url": url,
                "error": str(e),
            })
        time.sleep(SLEEP_SECONDS)

    df = pd.DataFrame(rows).sort_values(["player_id", "lastname", "firstname"], na_position="last")
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"\n✅ CSV exporté : {OUTPUT_CSV}")
    print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
