from src.parser import parse_patient, validate_patient

def test_parse_complete_patient():
    patient = {
        "resourceType": "Patient",
        "id": "123",
        "name": [
            {
                "family": "Martin",
                "given": ["Julie"]
            }
        ],
        "gender": "female",
        "birthDate": "1992-04-03"
    }

    result = parse_patient(patient)

    assert result["id"] == "123"
    assert result["given_name"] == "Julie"
    assert result["family_name"] == "Martin"
    assert result["gender"] == "female"
    assert result["birth_date"] == "1992-04-03"

def test_parse_patient_with_missing_fields():
    patient = {
        "resourceType": "Patient",
        "id": "456"
    }

    result = parse_patient(patient)

    assert result["id"] == "456"
    assert result["given_name"] is None
    assert result["family_name"] is None
    assert result["gender"] is None
    assert result["birth_date"] is None

def test_validate_patient_without_id():
    patient = {
        "id": None,
        "given_name": "Julie",
        "family_name": "Martin",
        "gender": "female",
        "birth_date": "1992-04-03"
    }

    result = validate_patient(patient)

    assert result is False

def test_validate_patient_with_id():
    patient = {
        "id": "123",
        "given_name": "Julie",
        "family_name": "Martin",
        "gender": "female",
        "birth_date": "1992-04-03"
    }           
    result = validate_patient(patient)

    assert result is True