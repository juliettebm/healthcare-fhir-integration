import logging

import pytest

from hl7.hl7_to_fhir import (
    parse_pid,
    convert_birth_date,
    convert_gender,
    find_pid_segment,
    get_ai_diagnostic
)
from ai.interop_assistant import (
    InvalidLLMResponseError,
    OllamaUnavailableError
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
        ("U", "unknown")
    ]
)
def test_convert_gender(hl7_gender, expected_fhir_gender):
    result = convert_gender(hl7_gender)

    assert result == expected_fhir_gender

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

def test_ollama_unavailable_does_not_break_pipeline(monkeypatch, caplog):
    def fake_diagnose_interop_error(error_message, hl7_message, severity):
        raise OllamaUnavailableError("connection refused")

    monkeypatch.setattr(
        "ai.interop_assistant.diagnose_interop_error",
        fake_diagnose_interop_error
    )

    with caplog.at_level(logging.WARNING):
        result = get_ai_diagnostic(
            "Aucun segment PID trouvé",
            "MSH|^~\\&|HOSPITAL_A|PARIS",
            "blocking"
        )

    assert result is None
    assert "Ollama indisponible" in caplog.text
    assert any(r.levelno == logging.WARNING for r in caplog.records)


def test_invalid_ai_response_does_not_break_pipeline(monkeypatch, caplog):
    def fake_diagnose_interop_error(error_message, hl7_message, severity):
        raise InvalidLLMResponseError("Diagnostic LLM invalide")

    monkeypatch.setattr(
        "ai.interop_assistant.diagnose_interop_error",
        fake_diagnose_interop_error
    )

    with caplog.at_level(logging.WARNING):
        result = get_ai_diagnostic(
            "Aucun segment PID trouvé",
            "MSH|^~\\&|HOSPITAL_A|PARIS",
            "blocking"
        )

    assert result is None
    assert "Réponse IA invalide" in caplog.text
    assert any(r.levelno == logging.ERROR for r in caplog.records)


def test_unexpected_ai_bug_is_not_masked(monkeypatch):
    def fake_diagnose_interop_error(error_message, hl7_message, severity):
        raise RuntimeError("bug")

    monkeypatch.setattr(
        "ai.interop_assistant.diagnose_interop_error",
        fake_diagnose_interop_error
    )

    with pytest.raises(RuntimeError):
        get_ai_diagnostic("erreur", "MSH|^~\\&|A|B", "blocking")


@pytest.mark.parametrize(
    "hl7_date, expected_fhir_date",
    [
        ("19920403", "1992-04-03"),
        ("199204", "1992-04"),
        ("1992", "1992"),
        ("20240229", "2024-02-29")
    ]
)
def test_convert_full_and_partial_birth_dates(hl7_date, expected_fhir_date):
    assert convert_birth_date(hl7_date) == expected_fhir_date


@pytest.mark.parametrize(
    "invalid_date",
    ["ABCDEFGH", "20260231", "20230229", "199213", "19920400", "0000", "19921", ""]
)
def test_convert_invalid_birth_date(invalid_date):
    assert convert_birth_date(invalid_date) is None


def test_invalid_birth_date_logs_warning(caplog):
    with caplog.at_level(logging.WARNING):
        convert_birth_date("20260231")

    assert "impossible" in caplog.text


def test_parse_pid_with_partial_birth_date():
    pid = "PID|1||PAT12345^^^HOSPITAL_A^MR||MARTIN^Julie||199204|F"

    result = parse_pid(pid)

    assert result["birthDate"] == "1992-04"


def test_unexpected_gender_logs_warning(caplog):
    with caplog.at_level(logging.WARNING):
        result = convert_gender("X")

    assert result == "unknown"
    assert "'X'" in caplog.text


def test_known_gender_does_not_log_warning(caplog):
    with caplog.at_level(logging.WARNING):
        convert_gender("F")

    assert caplog.records == []


def test_empty_gender_is_unknown_without_warning(caplog):
    with caplog.at_level(logging.WARNING):
        result = convert_gender("")

    assert result == "unknown"
    assert caplog.records == []
