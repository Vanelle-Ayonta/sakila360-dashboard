import mysql.connector
import pandas as pd
from sqlalchemy import create_engine, text
import os

MARIADB = dict(host="localhost", port=3306, user="root", password="12345", database="sakila_dwh")
SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sakila_dwh.db")

def export():
    print("Connexion MariaDB...")
    conn = mysql.connector.connect(**MARIADB)

    engine = create_engine(f"sqlite:///{SQLITE_PATH}", echo=False)
    print(f"SQLite : {SQLITE_PATH}\n")

    # dim_date, dim_customer, dim_store — export direct
    for table in ["dim_date", "dim_customer", "dim_store"]:
        df = pd.read_sql(f"SELECT * FROM {table}", conn)
        df.to_sql(table, engine, if_exists="replace", index=False)
        print(f"  {table:20s} : {len(df):>6,} lignes")

    # dim_film — enrichi avec rental_duration depuis sakila.film (durée autorisée)
    df_film = pd.read_sql("""
        SELECT df.*, sf.rental_duration AS duree_autorisee
        FROM sakila_dwh.dim_film df
        JOIN sakila.film sf ON sf.film_id = df.film_id
    """, conn)
    df_film.to_sql("dim_film", engine, if_exists="replace", index=False)
    print(f"  {'dim_film':20s} : {len(df_film):>6,} lignes  (+ duree_autorisee)")

    # fact_rental
    df_fr = pd.read_sql("SELECT * FROM fact_rental", conn)
    df_fr.to_sql("fact_rental", engine, if_exists="replace", index=False)
    print(f"  {'fact_rental':20s} : {len(df_fr):>6,} lignes")

    conn.close()

    # Vérification
    print("\nVérification SQLite :")
    with engine.connect() as c:
        for table in ["dim_date", "dim_film", "dim_customer", "dim_store", "fact_rental"]:
            n = c.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"  {table:20s} : {n:>6,} lignes")
        cols = [r[1] for r in c.execute(text("PRAGMA table_info(dim_film)")).fetchall()]
        print(f"\n  dim_film colonnes : {cols}")

    print("\nExport terminé.")

if __name__ == "__main__":
    export()
