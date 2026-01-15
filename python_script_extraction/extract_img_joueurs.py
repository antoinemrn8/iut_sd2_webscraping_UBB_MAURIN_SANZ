import re
import unicodedata
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# =========================
# CONFIGURATION
# =========================
ROSTER_URL = "https://www.ubbrugby.com/equipes/equipe-premiere/effectif.html"
BASE_DIR = Path(r"C:\Users\amaur\Documents\Etudes sup\2025-2026\S3\zSAE\SAE web scrapping")
PLAYERS_DIR = BASE_DIR / "Players"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Mots interdits (Staff, pubs, etc.)
BLACKLIST = ["entraineur", "manager", "staff", "preparateur", "kine", "medecin", "boutique", "billetterie", "partenaires"]

# =========================
# FONCTIONS INTELLIGENTES
# =========================
def build_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    retry = Retry(total=3, backoff_factor=1, status_forcelist=(429, 500, 502))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s

def clean_text(text):
    """Nettoie le texte : minuscule, sans accents, sans ponctuation."""
    if not text: return ""
    # Enlever les accents
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    text = text.lower()
    return text

def detect_folder(text):
    """
    Détermine le dossier en cherchant des mots-clés séparés.
    Plus robuste que de chercher une phrase exacte.
    """
    t = clean_text(text)
    
    # 1. Vérifier si c'est interdit
    if any(word in t for word in BLACKLIST):
        return "SKIP"

    # 2. Logique par combinaison de mots
    
    # 1ère Ligne
    if "pilier" in t or "talonneur" in t or ("1ere" in t and "ligne" in t):
        return "1ere_ligne"
    
    # 2ème Ligne (Cherche '2' et 'ligne', ou 'second' et 'ligne')
    if ("2" in t and "ligne" in t) or ("second" in t and "ligne" in t):
        return "2eme_ligne"
    
    # 3ème Ligne
    if ("3" in t and "ligne" in t) or ("troisieme" in t):
        return "3eme_ligne"
    
    # Charnière
    if "melee" in t or "ouverture" in t:
        return "charniere"
    
    # Trois-quarts
    if "ailier" in t or "centre" in t or "arriere" in t:
        if "centre de formation" in t: # Cas particulier : lien vers le centre de formation
            return "SKIP"
        if "arriere" in t: return "arriere"
        if "centre" in t: return "centre"
        if "ailier" in t: return "ailier"

    return "autres"

def extract_name(raw_text):
    """Extrait proprement le nom en enlevant les mots parasites."""
    words = raw_text.split()
    clean_parts = []
    
    # Mots à ne PAS mettre dans le nom de fichier
    banned_in_name = [
        "pilier", "talonneur", "ligne", "charniere", "melee", "ouverture", 
        "ailier", "centre", "arriere", "cm", "kg", "ans", "eme", "ere", "2", "3", "1"
    ]
    
    for w in words:
        w_clean = clean_text(w)
        # Si le mot n'est pas un chiffre et n'est pas un mot technique
        if not w_clean.isdigit() and w_clean not in banned_in_name:
            clean_parts.append(w)
    
    # On retourne les 2 premiers mots (Prénom Nom)
    return " ".join(clean_parts[:2])

def sanitize_filename(name):
    name = clean_text(name)
    name = re.sub(r'[^a-z0-9]', '_', name)
    return name.strip('_')

# =========================
# MAIN
# =========================
def main():
    print(f"🚀 Démarrage Scraping UBB...")
    session = build_session()
    
    try:
        r = session.get(ROSTER_URL, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"❌ Erreur connexion : {e}")
        return

    images = soup.find_all("img")
    print(f"🔍 {len(images)} images trouvées. Filtrage en cours...")
    
    count = 0
    seen = set()

    for img in images:
        img_url = img.get("data-src") or img.get("src")
        if not img_url or any(x in img_url for x in ["svg", "logo", "icon", "footer", "partenaires"]):
            continue
            
        full_url = urljoin(ROSTER_URL, img_url)
        if full_url in seen: continue

        # Remonter aux parents pour trouver le texte
        parent = img.parent
        found = False
        
        for _ in range(4):
            if parent:
                # Récupère tout le texte brut avec des espaces
                raw_text = parent.get_text(separator=" ")
                folder = detect_folder(raw_text)
                
                if folder == "SKIP":
                    found = True
                    break
                
                if folder != "autres":
                    # On a trouvé un joueur valide !
                    name_str = extract_name(raw_text)
                    
                    if len(name_str) > 2: # Nom valide
                        filename = f"{sanitize_filename(name_str)}.jpg"
                        dest = PLAYERS_DIR / folder
                        dest.mkdir(parents=True, exist_ok=True)
                        file_path = dest / filename
                        
                        if not file_path.exists():
                            try:
                                # Téléchargement
                                r_img = session.get(full_url, timeout=10)
                                with open(file_path, "wb") as f:
                                    f.write(r_img.content)
                                print(f"✅ [{folder}] {filename}")
                            except:
                                print(f"⚠️ Echec download: {name_str}")
                        
                        seen.add(full_url)
                        count += 1
                        found = True
                        break
                parent = parent.parent
            else:
                break
                
    print(f"\n🎉 Fini ! {count} joueurs récupérés.")

if __name__ == "__main__":
    main()
