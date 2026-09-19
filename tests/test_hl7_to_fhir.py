import pytest

from hl7.hl7_to_fhir import (
    parse_pid,
    convert_birth_date,
    convert_gender,
    find_pid_segment,
    get_ai_diagnostic
)

def test_message_without_pid():
    message = "MSH|^~\\&|HOSPITAL_A|PARIS"

    with pytest.raises(ValueError):
        find_pid_segment(message)

@pytest.mark.parametrize(
    "hl7_gender, expected_fhir_gender",
    [
        ("F", "female"),
        ("M", "male"),
        ("O", "other"),
        ("U", "unknown"),
        ("X", "unknown")
    ]
)
def test_convert_gender(hl7_gender, expected_fhir_gender):
    result = convert_gender(hl7_gender)

    assert result == expected_fhir_gender

def test_convert_birth_date():
    result = convert_birth_date("19920403")

    assert result == "1992-04-03"

def test_parse_pid():
    pid = "PID|1||PAT12345^^^HOSPITAL_A^MR||MARTIN^Julie||19920403|F"

    result = parse_pid(pid)

    assert result["resourceType"] == "Patient"
    assert result["identifier"][0]["value"] == "PAT12345"
    assert result["name"][0]["family"] == "MARTIN"
    assert result["name"][0]["given"][0] == "Julie"
    assert result["gender"] == "female"
    assert result["birthDate"] == "1992-04-03"

def test_parse_pid_without_given_name():
    pid = "PID|1||PAT12345^^^HOSPITAL_A^MR||MARTIN||19920403|F"

    result = parse_pid(pid)

    assert result["name"][0]["family"] == "MARTIN"
    assert "given" not in result["name"][0]

def test_parse_incomplete_pid():
    pid = "PID|1||PAT12345"

    with pytest.raises(ValueError):
        parse_pid(pid)

def test_ai_failure_does_not_break_pipeline(monkeypatch):
    def fake_diagnose_interop_error(error_message, hl7_message, severity):
        raise ConnectionError("Ollama unavailable")

    monkeypatch.setattr(
        "ai.interop_assistant.diagnose_interop_error",
        fake_diagnose_interop_error
    )

    result = get_ai_diagnostic(
        "Aucun segment PID trouvé",
        "MSH|^~\\&|HOSPITAL_A|PARIS",
        "blocking"
    )

    assert result is None

def test_convert_invalid_birth_date():
    assert convert_birth_date("ABCDEFGH") is None
    assert convert_birth_date("20260231") is None
    assert convert_birth_date("199204") is None