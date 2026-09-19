from src.database import (
    create_database,
    save_patients,
    get_all_patients
)


def test_save_and_get_patients(tmp_path):
    database_path = tmp_path / "test_patients.db"

    create_database(database_path)

    patients = [
        {
            "id": "PAT001",
            "given_name": "Julie",
            "family_name": "Martin",
            "gender": "female",
            "birth_date": "1992-04-03"
        }
    ]

    save_patients(patients, database_path)

    stored_patients = get_all_patients(database_path)

    assert len(stored_patients) == 1
    assert stored_patients[0] == (
        "PAT001",
        "Julie",
        "Martin",
        "female",
        "1992-04-03"
    )


def test_save_patients_replaces_existing_patient(tmp_path):
    database_path = tmp_path / "test_patients.db"

    create_database(database_path)

    first_version = [{
        "id": "PAT001",
        "given_name": "Julie",
        "family_name": "Martin",
        "gender": "female",
        "birth_date": "1992-04-03"
    }]

    updated_version = [{
        "id": "PAT001",
        "given_name": "Julia",
        "family_name": "Martin",
        "gender": "female",
        "birth_date": "1992-04-03"
    }]

    save_patients(first_version, database_path)
    save_patients(updated_version, database_path)

    stored_patients = get_all_patients(database_path)

    assert stored_patients == [
        ("PAT001", "Julia", "Martin", "female", "1992-04-03")
    ]
