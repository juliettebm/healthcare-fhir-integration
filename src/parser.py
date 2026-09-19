def parse_patient(patient):
    patient_id = patient.get("id")
    gender = patient.get("gender")
    birth_date = patient.get("birthDate")

    names = patient.get("name", [])

    if names:
        first_name = names[0]

        family_name = first_name.get("family")

        given_names = first_name.get("given", [])

        if given_names:
            given_name = given_names[0]
        else:
            given_name = None
    else:
        family_name = None
        given_name = None

    return {
        "id": patient_id,
        "given_name": given_name,
        "family_name": family_name,
        "gender": gender,
        "birth_date": birth_date
    }

def validate_patient(patient):
    if patient["id"] is None:
        return False

    return True