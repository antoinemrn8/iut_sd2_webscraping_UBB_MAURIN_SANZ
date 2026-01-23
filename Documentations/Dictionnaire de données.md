# Dictionnaire de données

## Structure du repo

iut_sd2_webscraping_UBB_MAURIN_SANZ/
│
├── Documentations/                    # Dossier pour avoir toutes les définitions etc
│   ├── Dictionnaire de données.md     # Contient la signification de toutes les abréviations
│   ├── html_view_sources.md           # Contient les liens de code source de pages scrapent
│   └── Structure repo                 
│
├── data/                              # Dossier contenant tous les fichiers utilisés pour le PBI
│   ├── CSVs/                          # Contient tous les fichiers csv scrapent
│      ├── classement_cup.csv
│      ├── classement_top14.csv
│      ├── players.csv
│      └── results.csv
│   ├── Meaning/                       # Contient les acronymes des noms de clubs au format csv
│      ├── Nom_CUP.csv
│      ├── Nom_TOP_14.csv
│      └── signification_classement.csv
│   ├── Players/                       # Contient les images png des joueurs de l'UBB par type de poste
│      ├── 1ere_ligne/                 
│      ├── 2eme_ligne/
│      ├── 3eme_ligne/
│      ├── ailier/
│      ├── arriere/
│      ├── centre/
│      └── charniere/
│   └── nationality/                  # Contient les le drapeaux des nationalités pour le tableau de bord
│
├── python_script_extraction/         # Dossier contenant tous les codes de scrap
│   ├── 0_extract_players.py          # Scrap des images des joueurs
│   ├── extract_classement.py         # Scrap des classements
│   ├── extract_classement_cup.py     # Scrap du classement de Champions Cup
│   ├── extract_classement_top14.py   # Scrap du classement du Top 14
│   ├── extract_img_players.py        # Scrap des images des joueurs
│   ├── extract_players.py            # Scrap des informations des joueurs
│   ├── extract_results.py            # Scrap des résulats du club
│   ├── photo_extract.py              # Scrap des images des joueurs
│   ├── test_flags.py                 # Scrap des images des drapeaux
│   └── url_extract.py                # Scrap des liens des images des joueurs
│
├── Rapport_UBB.pdf                   
└── README.md                         # Documentation du projet (Comment installer, comment lancer)

## Onglet **classement** :

| Abréviation | Signification |
| --- | --- |
| Pos | Position au classement |
| Équipe | Nom de l’équipe |
| Pts | Points au classement |
| MJ | Matchs joués |
| BO | Bonus offensifs (victoire avec bonus) |
| BD | Bonus défensifs (défaite de 7 points ou moins) |
| V | Victoires |
| N | Matchs nuls |
| D | Défaites |
| P. | Points marqués (points pour) |
| C. | Points encaissés (points contre) |
| Diff | Différence de points (P. − C.) |
| Prochain match | Prochaine rencontre programmée (adversaire, date et lieu) |


## Equipes **TOP 14** :

| Nom_court | Nom long |
| --- | --- |
| SP | Pau |
| ST | Stade Toulousain |
| SFP | Stade Français |
| UBB | Bordeaux-Bègles |
| MHR | Montpellier |
| RCT | Toulon |
| ASM | Clermont |
| ASR | La Rochelle |
| CO | Castres |
| AB | Bayonne |
| LOU | Lyon |
| R92 | Racing 92 |
| USM | Montauban |
| USAP | Perpignan |


## Equipes **Champions Cup** :

| Poule | Abréviation | Nom complet
| --- | --- | --- |
| 1 | SAR	| Saracens |
| 1	| SAL	| Sale |
| 1	| SHA	| The Sharks |
| 1	| GLA	| Glasgow |
| 1	| ST	| Stade Toulousain |
| 1	| ASM	| Clermont |
| 2	| BAT	| Bath |
| 2	| EDI	| Edimbourg |
| 2	| RCT	| Toulon |
| 2	| MUN	| Munster |
| 2	| GLO	| Gloucester |
| 2	| CO	| Castres |
| 3	| LEI	| Leinster |
| 3	| HAR	| Harlequins |
| 3	| STO	| Stormers |
| 3	| ASR	| La Rochelle |
| 3	| TIG	| Leicester |
| 3	| AB	| Bayonne |
| 4	| UBB	| Bordeaux-Bègles |
| 4	| BRI	| Bristol |
| 4	| NOR	| Northampton |
| 4	| SP	| Pau |
| 4	| SCA	| Scarlets |
| 4	| BUL	| Bulls |
