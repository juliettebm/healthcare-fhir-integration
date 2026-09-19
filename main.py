import requests

from src.fhir_client import get_patient_pages
from src.parser import parse_patient, validate_patient
from src.database import create_database, save_patients, get_all_patients


def main():
    create_database()

    patients_to_save = []

    try:
        for page_number, bundle in enumerate(get_patient_pages(), start=1):

            print(f"\n=== PAGE {page_number} ===")

            entries = bundle.get("entry", [])

            for entry in entries:
                patient = entry.get("resource")

                if patient is None:
                    print("Entrée ignorée : ressource FHIR absente")
                    continue

                parsed_patient = parse_patient(patient)

                if validate_patient(parsed_patient):
                    patients_to_save.append(parsed_patient)
                else:
                    print("Patient ignoré : identifiant manquant")

                print(parsed_patient)

    except requests.RequestException as error:
        print(f"Erreur lors de l'appel à l'API FHIR : {error}")
        return

    save_patients(patients_to_save)

    stored_patients = get_all_patients()

    print("\n=== PATIENTS EN BASE ===")
    print("Nombre de patients :", len(stored_patients))

    for patient in stored_patients:
        print(patient)


if __name__ == "__main__":
    main()