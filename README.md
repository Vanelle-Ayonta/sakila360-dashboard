# 🎬 Sakila 360 — Dashboard Data Warehouse

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.x-3F4F75?style=flat-square&logo=plotly&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3.x-003B57?style=flat-square&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/Licence-MIT-22c55e?style=flat-square)

> Tableau de bord analytique interactif pour explorer les performances d'une chaîne de location de films — construit sur un Data Warehouse en schéma en étoile et déployé avec Streamlit.

---

## 🎯 Objectif

Ce projet académique, réalisé à l'**ISSEA (Institut Sous-régional de Statistique et d'Économie Appliquée)**, vise à mettre en œuvre un Data Warehouse complet sur la base de données **Sakila** — une base fictive de chaîne de location de vidéos.

L'objectif est d'analyser la **performance commerciale** de la chaîne (chiffre d'affaires, retards, fidélité client, répartition géographique) à travers un pipeline ETL, un entrepôt de données en schéma en étoile, et un dashboard interactif multi-pages.

---

## 👥 Équipe

| Membre | Rôle |
|---|---|
| **AMBASSA Sammuel Lumière** | Modélisation & ETL |
| **AYONTA NDJOUTSE Vanelle** | Dashboard & Visualisation |
| **BAMOGO Karim** | Analyses OLAP & SQL |
| **M. TAPAMO** | Encadrant pédagogique |

> ISSEA — Promotion 2025-2026

---

## 🏗️ Architecture

Le Data Warehouse repose sur un **schéma en étoile** composé des tables suivantes :

```
fact_rental ──── dim_date       (730 jours)
     │      ──── dim_film       (1 000 films, 16 catégories)
     │      ──── dim_customer   (599 clients, 108 pays, 3 segments)
     └──────── dim_store       (2 magasins)
```

| Table | Lignes | Description |
|---|---|---|
| `fact_rental` | 15 861 | Transactions de location (grain : 1 ligne = 1 location) |
| `dim_date` | 730 | Calendrier enrichi (jour, mois, trimestre, année) |
| `dim_film` | 1 000 | Films avec catégorie, rating, durée autorisée |
| `dim_customer` | 599 | Clients segmentés (Fidèle / Régulier / Occasionnel) |
| `dim_store` | 2 | Magasins avec ville et adresse |

---

## 📊 Fonctionnalités du dashboard

Le dashboard est organisé en **6 pages** accessibles via la barre de navigation latérale :

| Page | Description |
|---|---|
| 📊 **Vue d'ensemble** | KPIs globaux (CA, locations, retards, pénalités, taux d'occupation), revenus mensuels, répartition trimestrielle |
| 📈 **Analyse temporelle** | Évolution mensuelle du CA par catégorie, courbe cumulative, heatmap mois × catégorie |
| 🎬 **Performances** | Top 15 films par CA et par jours de retard, volume par catégorie, taux d'occupation Q4 |
| 👥 **Clients** | Segmentation clientèle, top 20 clients, CA moyen par segment × catégorie, fréquence de location |
| 🌍 **Géographie** | Heatmap pays × catégorie, top 15 pays par CA, catégorie favorite par pays |
| 📋 **Données brutes** | Accès direct aux transactions filtrées avec export CSV |

### Filtres croisés disponibles

Chaque page applique en temps réel les filtres suivants :

- **Catégorie** — sélection multiple parmi les 16 catégories de films
- **Pays** — filtrage par pays du client
- **Magasin** — Store 1 (Canada) ou Store 2 (Australie)
- **Segment client** — Fidèle, Régulier ou Occasionnel
- **Année** — 2005 ou 2006

---

## 🚀 Lancement local

**Prérequis** : Python 3.11+

```bash
# 1. Cloner le dépôt
git clone https://github.com/vanelleayonta/sakila360-dashboard.git
cd sakila360-dashboard

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer le dashboard
streamlit run sakila360_dashboard.py

# 4. Ouvrir dans le navigateur
#    http://localhost:8501
```

> La base de données SQLite (`sakila_dwh.db`) est incluse dans le dépôt — aucune installation de serveur de base de données requise.

---

## 🌐 Démo en ligne

👉 [**Accéder au dashboard**](https://sakila360-dashboard.streamlit.app)

---

## 🛠️ Stack technique

| Technologie | Usage |
|---|---|
| **Python 3.11** | Langage principal |
| **Streamlit** | Framework web & interface |
| **Plotly** | Graphiques interactifs (Express + Graph Objects) |
| **SQLite** | Base de données portable (schéma en étoile) |
| **SQLAlchemy 2.0** | ORM & connexion à la base |
| **Pandas** | Manipulation et transformation des données |

---

## 📁 Structure du projet

```
sakila360-dashboard/
├── sakila360_dashboard.py        # Application principale Streamlit
├── sakila_dwh.db                 # Base de données SQLite (DWH complet)
├── requirements.txt              # Dépendances Python
├── export_to_sqlite.py           # Script ETL MariaDB → SQLite
├── Rapport.pdf                   # Rapport académique (PDF)
├── Rapport.docx                  # Rapport académique (Word)
├── .gitignore
└── README.md
```

---

## 📈 Analyses OLAP implémentées

Les quatre analyses OLAP du cahier des charges sont intégrées dans le dashboard :

1. **Analyse 1 — Roll-up mensuel × catégories**
   Agrégation du CA par mois et par catégorie de film, avec focus sur le Top 5. Visualisée via un graphique en barres groupées et une heatmap mois × catégorie.

2. **Analyse 2 — Top films par jours de retard**
   Identification des films générant le plus de jours de retard cumulés. Croisement avec la durée autorisée (`duree_autorisee`) pour calculer les dépassements réels.

3. **Analyse 3 — Corrélation pays × catégorie**
   Heatmap des volumes de location par pays et catégorie sur les 20 pays les plus actifs. Mise en évidence des préférences culturelles par région.

4. **Analyse 4 — Taux d'occupation inventaire Q4**
   Ratio films loués / films disponibles sur le quatrième trimestre, avec liste des films jamais loués sur la période.

---

## 📄 Licence

Ce projet est distribué sous licence **MIT**.
Libre d'utilisation, de modification et de redistribution avec mention des auteurs originaux.

---

<div align="center">
  <sub>Sakila 360 · ISSEA 2025-2026 · Encadrant : M. TAPAMO</sub>
</div>
