import json
from datetime import datetime

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
    if len(birth_date) != 8 or not birth_date.isdigit():
        return None

    try:
        datetime.strptime(birth_date, "%Y%m%d")
    except ValueError:
        return None

    return f"{birth_date[0:4]}-{birth_date[4:6]}-{birth_date[6:8]}"


def convert_gender(gender):
    gender_mapping = {
        "F": "female",
        "M": "male",
        "O": "other",
        "U": "unknown"
    }

    return gender_mapping.get(gender, "unknown")

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
    try:
        from ai.interop_assistant import diagnose_interop_error

        return diagnose_interop_error(
            error_message,
            hl7_message,
            severity
        )

    except Exception:
        return None


if __name__ == "__main__":
    message = read_hl7_message("hl7/sample_message.hl7")

    try:
        pid_segment = find_pid_segment(message)
        fhir_patient = parse_pid(pid_segment)

        save_fhir_patient(fhir_patient, "hl7/patient.json")

        print("Patient FHIR créé : hl7/patient.json")

    except ValueError as error:
        print("Erreur d'interopérabilité détectée :", error)

        diagnostic = get_ai_diagnostic(
            str(error),
            message,
            "blocking"
        )

        if diagnostic is not None:
            print("Diagnostic IA :")
            print(json.dumps(diagnostic, indent=4, ensure_ascii=False))

        else:
            print("Diagnostic IA indisponible.")