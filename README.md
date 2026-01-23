# Projet de Web Scraping : Analyse des données de l'Union Bordeaux-Bègles (UBB)

## 1. Description du projet
Ce projet a été réalisé dans le cadre de la SAé "Collecte Automatisée de données web". Il vise à mettre en œuvre un pipeline complet de traitement de données (ETL) extraites du web.

**Objectif :**
L'objectif est de récupérer et d'analyser les performances du club de rugby **Union Bordeaux-Bègles (UBB)**. Le projet se concentre sur deux axes principaux :
1.  **Statistiques globales du club :** Récupération du classement actuel (Top 14 / Champions Cup), points, victoires/défaites.
2.  **Comparaison par joueurs :** Extraction des fiches individuelles (postes, temps de jeu, essais marqués, statistiques de défense) pour permettre une comparaison intra-équipe.

## 2. Prérequis techniques
Pour exécuter ce projet, l'environnement suivant est nécessaire :

* **Langage :** Python 3.x
* **Gestionnaire de paquets :** pip
* **Installation des dépendances :**
    ```bash
    pip install requests beautifulsoup4
    ```

## 3. Librairies utilisées
Le projet repose sur l'écosystème Python. Le choix des librairies a été motivé par la nécessité de naviguer dans le DOM.

### Bibliothèques tierces (Externes)
* **Requests** (`requests`, `HTTPAdapter`, `Retry`) :
    * Utilisée pour effectuer les requêtes HTTP (GET) vers les sites de l'UBB et de la ligue.
    * *Justification :* L'ajout de `HTTPAdapter` et `Retry` nous permet de gérer automatiquement les erreurs de connexion et de ré-essayer en cas d'échec, rendant le scraper plus robuste face aux coupures réseau.
* **BeautifulSoup4** (`bs4`) :
    * Utilisée pour le parsing du code HTML récupéré.
    * *Justification :* Elle permet de naviguer simplement dans l'arborescence du DOM (parents/enfants) et de cibler les données via des classes CSS ou des ID, simulant l'approche de Jsoup en Java.

### Bibliothèques standard (Natives)
* **Time** (`time`) :
    * Utilisée pour introduire des pauses (`time.sleep`) entre les requêtes.
    * *Justification :* Essentiel pour respecter l'éthique du scraping et éviter de surcharger les serveurs cibles.
* **Re** (`re`) :
    * Utilisée pour les expressions régulières (Regex).
    * *Justification :* Permet un nettoyage fin des données (ex: extraire uniquement les chiffres d'une chaîne "80 min", supprimer les espaces superflus).
* **Unicodedata** (`unicodedata`) :
    * Utilisée pour la normalisation du texte.
    * *Justification :* Permet de gérer les encodages et de transformer les caractères spéciaux (accents) pour uniformiser les noms des joueurs ou les villes.
* **Urllib & Pathlib** (`urllib.parse`, `pathlib`) :
    * Utilisées pour la manipulation sécurisée des URLs (jointures) et la gestion compatible (Windows/Mac/Linux) des chemins de fichiers pour l'export des données.

## 4. Étapes pour reproduire le projet // Répartition des rôles
Conformément aux consignes du projet en binôme, les responsabilités ont été réparties comme suit :

* **Préalable : Vérification de la légalité (Robots.txt)**
   * [cite_start]Avant tout scraping, nous avons identifié des sources autorisant la collecte automatisée[cite: 139].
   * Action :** Vérifier l'URL `site-cible.com/robots.txt`.
   * Critère :** S'assurer que les chemins d'accès aux données des joueurs et du classement ne sont pas en `Disallow`.

* **Étape 1 : Analyse & Extraction (Responsable : Antoine)**
    * Identification des sources de données et analyse du DOM.
    * Développement des scripts de scraping pour récupérer le contenu HTML brut.
    * Gestion des requêtes HTTP et contournement basique des protections (User-Agent).

* **Étape 2 : Traitement & Export (Responsable : Rafaël)**
    * Nettoyage des données brutes (suppression des balises, formatage des nombres/dates).
    * Structuration des données.
    * Implémentation de l'export vers un format exploitable (CSV / JSON).

* **Étape 3 : Visualisation & Interprétation (Travail commun)**
    * Création des graphiques et tableaux de bord (via [Excel / PowerBI / D3.js - *Choisis ton outil*]).
    * Analyse critique des résultats obtenus et rédaction des conclusions.
 
Liens utiles :
* [Tableau de bord](https://[github.com](https://raw.githubusercontent.com/antoinemrn8/iut_sd2_webscraping_UBB_MAURIN_SANZ/blob/main/power_BI/UBB_analyse.pbix)
* []()
