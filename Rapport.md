# Sans titre

# 1. Introduction

Dans le cadre de notre module de Web Scraping, nous avons souhaité orienter notre projet vers un domaine qui nous passionne : le sport. Lors de la phase de brainstorming avec mon binôme, le choix du rugby s'est imposé comme une évidence.

Étant un fervent supporter de l'**Union Bordeaux Bègles (UBB)**, j'ai suggéré de concentrer nos efforts sur ce club. Ce choix est motivé par deux facteurs principaux :

1. **L'intérêt personnel :** Travailler sur un sujet que l'on maîtrise permet une meilleure critique et analyse des données récoltées.
2. **La richesse des données :** Un club de Top 14 génère une quantité importante de statistiques (performances des joueurs, historique des matchs, effectifs) qui se prêtent parfaitement à la création d'un tableau de bord décisionnel.

L'objectif de ce rapport est de détailler notre démarche technique, de la collecte des données à leur visualisation dans un outil de Business Intelligence.

# 2. Liste des sites web choisis

Pour réaliser ce projet, nous nous sommes concentrés sur la source officielle et la plus fiable concernant le club.

- **Site principal :** Site officiel de l'Union Bordeaux Bègles
- **URL :** `https://www.ubbrugby.com` (ou l'URL exacte que vous avez utilisée)

Ce site centralise l'ensemble des informations nécessaires : fiches des joueurs, calendrier, résultats et actualités du club.

# 3. Légalité et Éthique (Robots.txt)

Avant de lancer le moindre script de récupération de données, nous nous sommes assurés de respecter la politique du site web en matière de scraping. Cette étape est cruciale pour garantir la légalité de notre démarche et ne pas surcharger les serveurs du club.

Nous avons consulté le fichier `robots.txt` situé à la racine du site (`https://www.ubbrugby.com/robots.txt`).

**Analyse du fichier :**
L'analyse a révélé que le site est très ouvert quant à l'indexation et au crawling. Nous avons constaté les directives suivantes :

- `User-agent: *` : Les règles s'appliquent à tous les robots.
- `Allow: /` : L'accès est autorisé depuis la racine du site.

Aucune restriction majeure ne bloquant l'accès aux pages de statistiques ou d'effectif, nous avons pu procéder à l'élaboration de nos scripts en toute légalité.

![image.png](image.png)

# 4. Résultats

## 4.1. Processus technique

Notre pipeline de données s'est déroulé en trois phases :

1. **Le Scraping :** Nous avons développé des scripts (en Python/R) pour extraire les informations ciblées. Nous avons récupéré non seulement des données textuelles et chiffrées, mais également les fichiers images (photos des joueurs, logos).
2. **Le Nettoyage (Data Cleaning) :** Les données brutes extraites ont été stockées dans des fichiers `.csv`. Une phase de nettoyage a été nécessaire pour normaliser les noms, gérer les valeurs manquantes et typer correctement les statistiques afin de les rendre exploitables.
3. **La Visualisation :** Importation des données propres dans PowerBI.

## 4.2. Présentation du Tableau de Bord

Le produit fini est un rapport PowerBI interactif composé de 4 onglets, permettant une navigation du général au particulier.

### Onglet 1 : Contexte du projet

Cette page d'accueil présente le cadre de l'étude, la méthodologie employée et les sources. Elle sert d'introduction à l'utilisateur du tableau de bord.

### Onglet 2 : Statistiques globales du club

Cet onglet offre une vue macroscopique de la saison de l'UBB. Il permet d'analyser les performances collectives de l'équipe (classement, points marqués/encaissés, ratio de victoires).

![image.png](image%201.png)

### Onglet 3 : Statistiques individuelles (Joueurs)

C'est le cœur de notre base de données. Cet onglet permet d'explorer l'effectif avec des fonctionnalités de filtrage avancées :

- Filtrage par joueur spécifique.
- Segmentation par tranche d'âge.
- Analyse par poste ou nationalité.

![image.png](image%202.png)

### Onglet 4 : Comparateur de joueurs

Pour aller plus loin dans l'analyse technique, nous avons créé un outil de comparaison directe (Head-to-Head). Il permet de sélectionner deux joueurs et de confronter leurs statistiques côte à côte, ce qui est particulièrement utile pour comparer des profils évoluant au même poste.

![image.png](image%203.png)

# 5. Conclusion suite à l'analyse

Ce projet nous a permis de valider l'ensemble de la chaîne de traitement de la donnée, de l'extraction brute sur le web jusqu'à la prise de décision visuelle.

Le choix de l'UBB s'est avéré payant : la qualité des données disponibles sur leur site a permis de construire un tableau de bord complet et fonctionnel. Nous avons réussi à transformer des informations éparses sur le web en un outil d'analyse structuré.

Pour aller plus loin, nous pourrions envisager d'automatiser ce script pour qu'il s'exécute chaque semaine afin de mettre à jour le tableau de bord après chaque journée de Top 14.
