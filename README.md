# 🎬 Sakila 360 — Dashboard Data Warehouse

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Plotly](https://img.shields.io/badge/Plotly-5.x-3F4F75?style=flat&logo=plotly&logoColor=white)](https://plotly.com)
[![SQLite](https://img.shields.io/badge/SQLite-3.x-003B57?style=flat&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/Licence-MIT-green?style=flat)](LICENSE)

> Analyse décisionnelle de la performance d'une chaîne de location de films via un entrepôt de données en schéma en étoile — projet académique ISSEA 2025-2026.

---

## 🌐 Démo en ligne

**👉 [Accéder au dashboard Sakila 360](https://vanelle-ayonta-sakila360-dashboard.streamlit.app/)**

Le dashboard est accessible publiquement, sans installation requise.

---

## 🎯 Objectif

Le management de la chaîne **Sakila** souhaite analyser la rentabilité de ses films et le comportement de ses clients pour optimiser son stock et ses campagnes marketing. Ce projet répond à cet objectif en construisant un **Data Warehouse décisionnel** à partir de la base transactionnelle Sakila, et en exposant les résultats via un dashboard analytique interactif.

---

## 👥 Équipe

| Membre | Rôle |
|--------|------|
| **AMBASSA Sammuel Lumière** | Développement & Analyse |
| **AYONTA NDJOUTSE Vanelle** | Développement & Analyse |
| **BAMOGO Karim** | Développement & Analyse |
| **M. TAPAMO** | Encadrant |

**Institution :** ISSEA — Institut Sous-régional de Statistique et d'Économie Appliquée
**Année académique :** 2025-2026

---

## 🏗️ Architecture — Schéma en étoile

```
                    ┌─────────────┐
                    │  dim_date   │
                    │  730 jours  │
                    └──────┬──────┘
                           │
┌──────────────┐    ┌──────┴──────┐    ┌───────────────┐
│   dim_film   │    │ fact_rental │    │ dim_customer  │
│  1 000 films ├────┤  15 861 loc.├────┤  599 clients  │
│ 16 catégories│    │             │    │  108 pays     │
└──────────────┘    └──────┬──────┘    └───────────────┘
                           │
                    ┌──────┴──────┐
                    │  dim_store  │
                    │  2 magasins │
                    └─────────────┘
```

| Table | Lignes | Description |
|-------|--------|-------------|
| `fact_rental` | 15 861 | Transactions de location |
| `dim_date` | 730 | Calendrier 2005-2006 |
| `dim_film` | 1 000 | Films avec catégorie, rating, langue |
| `dim_customer` | 599 | Clients avec pays et segment |
| `dim_store` | 2 | Magasins avec manager |

---

## 📊 Fonctionnalités du dashboard

Le dashboard est organisé en **6 pages** avec des filtres croisés (Catégorie, Pays, Magasin, Segment client) appliqués globalement.

| Page | Contenu |
|------|---------|
| **Vue d'ensemble** | KPIs globaux, revenus mensuels, segments clients, distribution des durées |
| **Analyse temporelle** | CA mensuel par catégorie, courbe cumulative, heatmap mois × catégorie |
| **Performances** | Top films par CA et retards, classement catégories, taux d'occupation Q4 |
| **Clients** | Segmentation, top 20 clients, comportement par segment, fréquence de location |
| **Géographie** | Heatmap pays × catégorie, top pays par CA, catégorie favorite par marché |
| **Données brutes** | Export CSV des transactions filtrées |

---

## 📈 Analyses OLAP implémentées

1. **Analyse temporelle** — Évolution mensuelle du chiffre d'affaires par catégorie de film sur 2005
2. **Top performances** — Top 5 films générateurs de pénalités de retard par magasin
3. **Profilage client** — Corrélation entre pays d'origine du client et catégorie de film louée
4. **Taux d'occupation** — Pourcentage de films de l'inventaire non loués au dernier trimestre (4,2%)

---

## 🚀 Lancement en local

### Prérequis
- Python 3.11+
- pip

### Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/Vanelle-Ayonta/sakila360-dashboard.git
cd sakila360-dashboard

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer le dashboard
streamlit run sakila360_dashboard.py

# 4. Ouvrir dans le navigateur
# http://localhost:8501
```

---

## 🛠️ Stack technique

| Outil | Usage |
|-------|-------|
| **Python 3.11** | Langage principal |
| **Streamlit** | Framework dashboard |
| **Plotly** | Visualisations interactives |
| **SQLite** | Base de données embarquée |
| **SQLAlchemy** | Connexion base de données |
| **Pandas** | Manipulation des données |

---

## 📁 Structure du projet

```
sakila360-dashboard/
├── sakila360_dashboard.py    # Application Streamlit principale
├── sakila_dwh.db             # Base de données SQLite (Data Warehouse)
├── requirements.txt          # Dépendances Python
├── Rapport_Sakila360_DWH.docx # Rapport académique complet
├── .gitignore
└── README.md
```

---

## 📄 Licence

MIT — Libre d'utilisation à des fins académiques et éducatives.

---

<div align="center">
  <sub>Projet Data Warehouse · ISSEA 2025-2026 · AMBASSA · AYONTA NDJOUTSE · BAMOGO · M. TAPAMO</sub>
</div>
