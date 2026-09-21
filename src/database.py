"""Persistance SQLite des patients FHIR.

Crée la table `patients` et y enregistre les patients validés avec
`INSERT OR REPLACE` sur l'`id` FHIR : relancer le pipeline met à jour les
lignes existantes au lieu de les dupliquer.

Outils : `sqlite3` (bibliothèque standard).
Sortie : patients.db (non versionnée, voir .gitignore).
"""
import sqlite3


DATABASE_NAME = "patients.db"


def create_database(database_name=DATABASE_NAME):
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            given_name TEXT,
            family_name TEXT,
            gender TEXT,
            birth_date TEXT
        )
    """)

    connection.commit()
    connection.close()


def save_patients(patients, database_name=DATABASE_NAME):
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()

    for patient in patients:
        cursor.execute("""
            INSERT OR REPLACE INTO patients (
                id,
                given_name,
                family_name,
                gender,
                birth_date
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            patient["id"],
            patient["given_name"],
            patient["family_name"],
            patient["gender"],
            patient["birth_date"]
        ))

    connection.commit()
    connection.close()


def get_all_patients(database_name=DATABASE_NAME):
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM patients")
    patients = cursor.fetchall()

    connection.close()

    return patients