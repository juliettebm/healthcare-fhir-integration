"""Normalisation et validation des ressources FHIR `Patient`.

Transforme une ressource `Patient` brute en dictionnaire plat (id, prénom,
nom, genre, date de naissance). Les champs facultatifs de FHIR (`name`,
`gender`, `birthDate`) peuvent manquer : un champ absent devient `None` et ne
fait jamais planter le pipeline. Un patient sans `id` est jugé invalide, car
l'`id` sert de clé en base.

Outils : bibliothèque standard uniquement.
"""
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