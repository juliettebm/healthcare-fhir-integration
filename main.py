"""Pipeline FHIR -> SQLite.

Interroge le serveur de test public HAPI FHIR (R4), parcourt les pages de
`Bundle` de ressources `Patient`, normalise et valide chaque patient, puis
les enregistre dans SQLite. Les données reçues d'un serveur externe sont
souvent partielles : mieux vaut écarter ce qui est inutilisable que polluer
la base.

Outils : `requests` (src/fhir_client.py), parsing défensif (src/parser.py),
`sqlite3` avec upsert idempotent (src/database.py).

Sortie : patients.db, table `patients` (non versionnée). Relancer le script
met à jour les lignes existantes au lieu de les dupliquer. Le nombre de pages
est plafonné à 3 pour ne pas surcharger le serveur public.

Usage :
    python main.py
"""
import logging

import requests

from src.fhir_client import get_patient_pages
from src.parser import parse_patient, validate_patient
from src.database import create_database, save_patients, get_all_patients

logger = logging.getLogger(__name__)


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
                    logger.warning("Entrée ignorée : ressource FHIR absente")
                    continue

                parsed_patient = parse_patient(patient)

                if validate_patient(parsed_patient):
                    patients_to_save.append(parsed_patient)
                else:
                    logger.warning("Patient ignoré : identifiant manquant")

                print(parsed_patient)

    except requests.RequestException as error:
        logger.error("Erreur lors de l'appel à l'API FHIR : %s", error)
        return

    save_patients(patients_to_save)

    stored_patients = get_all_patients()

    print("\n=== PATIENTS EN BASE ===")
    print("Nombre de patients :", len(stored_patients))

    for patient in stored_patients:
        print(patient)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s : %(message)s"
    )
    main()