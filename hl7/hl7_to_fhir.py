import json
import logging
from datetime import date

logger = logging.getLogger(__name__)


def parse_pid(pid_segment):
    fields = pid_segment.split("|")

    if len(fields) < 9:
        raise ValueError("Segment PID incomplete")

    patient_identifier = fields[3]
    patient_name = fields[5]
    birth_date = fields[7]
    gender = fields[8]

    identifier_components = patient_identifier.split("^")
    name_components = patient_name.split("^")

    identifier = identifier_components[0]
    family_name = name_components[0]

    if len(name_components) > 1:
        given_name = name_components[1]
    else:
        given_name = None

    fhir_birth_date = convert_birth_date(birth_date)
    fhir_gender = convert_gender(gender)

    fhir_name = {
        "family": family_name
    }

    if given_name is not None:
        fhir_name["given"] = [given_name]

    fhir_patient = {
        "resourceType": "Patient",
        "identifier": [
            {
                "value": identifier
            }
        ],
        "name": [fhir_name],
        "gender": fhir_gender,
        "birthDate": fhir_birth_date
    }

    return fhir_patient

def convert_birth_date(birth_date):
    """Convertit une date HL7 (YYYY, YYYYMM ou YYYYMMDD) en date FHIR."""
    if not birth_date:
        return None

    if len(birth_date) not in (4, 6, 8) or not birth_date.isdigit():
        logger.warning("Date de naissance HL7 non reconnue : valeur ignorée")
        return None

    year = int(birth_date[0:4])
    month = int(birth_date[4:6]) if len(birth_date) >= 6 else 1
    day = int(birth_date[6:8]) if len(birth_date) == 8 else 1

    try:
        date(year, month, day)
    except ValueError:
        logger.warning("Date de naissance HL7 impossible : valeur ignorée")
        return None

    if len(birth_date) == 4:
        return birth_date[0:4]

    if len(birth_date) == 6:
        return f"{birth_date[0:4]}-{birth_date[4:6]}"

    return f"{birth_date[0:4]}-{birth_date[4:6]}-{birth_date[6:8]}"


GENDER_MAPPING = {
    "F": "female",
    "M": "male",
    "O": "other",
    "U": "unknown"
}


def convert_gender(gender):
    if gender in GENDER_MAPPING:
        return GENDER_MAPPING[gender]

    if gender:
        logger.warning(
            "Code de sexe HL7 inattendu %r : normalisé en 'unknown'",
            gender
        )

    return "unknown"

def read_hl7_message(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        message = file.read()
    return message


def find_pid_segment(message):
    segments = message.splitlines()

    for segment in segments:
        if segment.startswith("PID|"):
            return segment

    raise ValueError("Aucun segment PID trouvé")

def save_fhir_patient(patient, file_path):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(patient, file, indent=4, ensure_ascii=False)

def get_ai_diagnostic(error_message, hl7_message, severity):
    """Demande un diagnostic à l'assistant IA local.

    Une panne de l'IA ne doit jamais casser le pipeline : on journalise
    et on renvoie None.
    """
    try:
        from ai.interop_assistant import (
            InvalidLLMResponseError,
            OllamaUnavailableError,
            diagnose_interop_error,
        )
    except ImportError as error:
        logger.warning("Assistant IA non disponible : %s", error)
        return None

    try:
        return diagnose_interop_error(
            error_message,
            hl7_message,
            severity
        )

    except OllamaUnavailableError as error:
        logger.warning("Ollama indisponible, diagnostic IA ignoré : %s", error)

    except InvalidLLMResponseError as error:
        logger.error("Réponse IA invalide, diagnostic ignoré : %s", error)

    return None


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s : %(message)s"
    )

    message = read_hl7_message("hl7/sample_message.hl7")

    try:
        pid_segment = find_pid_segment(message)
        fhir_patient = parse_pid(pid_segment)

        save_fhir_patient(fhir_patient, "hl7/patient.json")

        logger.info("Patient FHIR créé : hl7/patient.json")

    except ValueError as error:
        logger.error("Erreur d'interopérabilité détectée : %s", error)

        diagnostic = get_ai_diagnostic(
            str(error),
            message,
            "blocking"
        )

        if diagnostic is not None:
            print("Diagnostic IA :")
            print(json.dumps(diagnostic, indent=4, ensure_ascii=False))
