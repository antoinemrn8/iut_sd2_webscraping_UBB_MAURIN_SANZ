# iut_sd2_webscraping_UBB_MAURIN_SANZ
# Projet de Web Scraping : Analyse des données de l'Union Bordeaux-Bègles (UBB)

## 1. Description du projet
Ce projet a été réalisé dans le cadre de la SAé "Collecte Automatisée de données web". Il vise à mettre en œuvre un pipeline complet de traitement de données (ETL) extraites du web.

**Objectif :**
L'objectif est de récupérer et d'analyser les performances du club de rugby **Union Bordeaux-Bègles (UBB)**. Le projet se concentre sur deux axes principaux :
1.  **Statistiques globales du club :** Récupération du classement actuel (Top 14 / Champions Cup), points, victoires/défaites.
2.  **Comparaison par joueurs :** Extraction des fiches individuelles (postes, temps de jeu, essais marqués, statistiques de défense) pour permettre une comparaison intra-équipe.

## 2. Répartition des rôles
Conformément aux consignes du projet en binôme, les responsabilités ont été réparties comme suit :

* **Partie 1 : Analyse & Extraction (Responsable : Antoine)**
    * Identification des sources de données et analyse du DOM.
    * Développement des scripts de scraping pour récupérer le contenu HTML brut.
    * Gestion des requêtes HTTP et contournement basique des protections (User-Agent).

* **Partie 2 : Traitement & Export (Responsable : Rafaël)**
    * Nettoyage des données brutes (suppression des balises, formatage des nombres/dates).
    * Structuration des données.
    * Implémentation de l'export vers un format exploitable (CSV / JSON).

* **Partie 3 : Visualisation & Interprétation (Travail commun)**
    * Création des graphiques et tableaux de bord (via [Excel / PowerBI / D3.js - *Choisis ton outil*]).
    * Analyse critique des résultats obtenus et rédaction des conclusions.

## 3. Prérequis techniques
Pour exécuter ce projet, vous avez besoin de :

* **Langage :** [Java version X / Python version X]
* **Outil de build :** [Maven / Gradle / Pip]
* **IDE suggéré :** [IntelliJ / Eclipse / VS Code]

## 4. Librairies utilisées
Le choix des technologies s'est porté sur :

* **Jsoup** (Java) : Pour le parsing HTML et l'extraction des nœuds DOM.
* **OpenCSV** (Java) : Pour l'écriture des fichiers de sortie.
* **[Autre librairie]** : [Description courte].

## 5. Architecture du projet
```text
/src
  /main
    /java
      /extraction    <-- Code d'Antoine (Scrapers)
      /processing    <-- Code de Rafaël (Nettoyage, Objets Métier)
      /export        <-- Code de Rafaël (Génération CSV/JSON)
  /resources         <-- Fichiers de configuration
/data                <-- Dossier où les fichiers .csv/.json sont générés
README.md
pom.xml (ou requirements.txt)
