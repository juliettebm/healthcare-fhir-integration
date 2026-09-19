import sqlite3


DATABASE_NAME = "patients.db"


def create_database():
    connection = sqlite3.connect(DATABASE_NAME)

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

def save_patients(patients):
    connection = sqlite3.connect(DATABASE_NAME)

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

def get_all_patients():
    connection = sqlite3.connect(DATABASE_NAME)

    cursor = connection.cursor()

    cursor.execute("SELECT * FROM patients")

    patients = cursor.fetchall()

    connection.close()

    return patients