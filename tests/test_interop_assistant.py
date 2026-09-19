import pytest
import requests

from ai.interop_assistant import (
    validate_diagnostic,
    build_error_context,
    diagnose_interop_error,
    call_ollama,
    InvalidLLMResponseError,
    OllamaUnavailableError
)

def test_build_error_context_with_severity():
    context = build_error_context(
        "Aucun segment PID trouvé",
        "MSH|^~\\&|HOSPITAL_A|PARIS",
        "blocking"
    )

    assert context["error_message"] == "Aucun segment PID trouvé"
    assert context["hl7_message"] == "MSH|^~\\&|HOSPITAL_A|PARIS"
    assert context["severity"] == "blocking"


def test_validate_complete_diagnostic():
    diagnostic = {
        "error_type": "missing_segment",
        "severity": "blocking",
        "hl7_element": "PID",
        "fhir_impact": "Patient resource cannot be generated",
        "explanation": "The PID segment is missing.",
        "suggested_action": "Verify the source HL7 message."
    }

    result = validate_diagnostic(diagnostic)

    assert result is True


def test_validate_incomplete_diagnostic():
    diagnostic = {
        "error_type": "missing_segment",
        "severity": "blocking"
    }

    result = validate_diagnostic(diagnostic)

    assert result is False

def test_validate_diagnostic_with_invalid_severity():
    diagnostic = {
        "error_type": "missing_segment",
        "severity": 2,
        "hl7_element": "PID",
        "fhir_impact": "Patient resource cannot be generated",
        "explanation": "The PID segment is missing.",
        "suggested_action": "Verify the source HL7 message."
    }

    result = validate_diagnostic(diagnostic)

    assert result is False

def test_pipeline_severity_overrides_llm_severity(monkeypatch):
    fake_llm_response = {
        "error_type": "missing_segment",
        "severity": "warning",
        "hl7_element": "PID",
        "fhir_impact": "Patient resource cannot be generated",
        "explanation": "The PID segment is missing.",
        "suggested_action": "Verify the source HL7 message."
    }

    def fake_call_ollama(prompt):
        return fake_llm_response

    monkeypatch.setattr(
        "ai.interop_assistant.call_ollama",
        fake_call_ollama
    )

    result = diagnose_interop_error(
        "Aucun segment PID trouvé",
        "MSH|^~\\&|HOSPITAL_A|PARIS",
        "blocking"
    )

    assert result["severity"] == "blocking"

def test_invalid_llm_output_is_rejected(monkeypatch):
    def fake_call_ollama(prompt):
        return {
            "error_type": "HL7 Parsing Error",
            "severity": "blocking"
        }

    monkeypatch.setattr(
        "ai.interop_assistant.call_ollama",
        fake_call_ollama
    )

    with pytest.raises(ValueError, match="Diagnostic LLM invalide"):
        diagnose_interop_error(
            "Aucun segment PID trouvé",
            "MSH|^~\\&|HOSPITAL_A|PARIS",
            "blocking"
        )


class FakeResponse:
    def __init__(self, json_data=None, status_error=None):
        self._json_data = json_data
        self._status_error = status_error

    def raise_for_status(self):
        if self._status_error:
            raise self._status_error

    def json(self):
        return self._json_data


def test_ollama_connection_error_is_reported_as_unavailable(monkeypatch):
    def fake_post(*args, **kwargs):
        raise requests.ConnectionError("connection refused")

    monkeypatch.setattr("ai.interop_assistant.requests.post", fake_post)

    with pytest.raises(OllamaUnavailableError):
        call_ollama("prompt")


def test_ollama_http_error_is_reported_as_unavailable(monkeypatch):
    def fake_post(*args, **kwargs):
        return FakeResponse(status_error=requests.HTTPError("500"))

    monkeypatch.setattr("ai.interop_assistant.requests.post", fake_post)

    with pytest.raises(OllamaUnavailableError):
        call_ollama("prompt")


def test_ollama_non_json_content_is_reported_as_invalid(monkeypatch):
    def fake_post(*args, **kwargs):
        return FakeResponse({"message": {"content": "pas du JSON"}})

    monkeypatch.setattr("ai.interop_assistant.requests.post", fake_post)

    with pytest.raises(InvalidLLMResponseError):
        call_ollama("prompt")


def test_ollama_unexpected_payload_is_reported_as_invalid(monkeypatch):
    def fake_post(*args, **kwargs):
        return FakeResponse({"unexpected": "payload"})

    monkeypatch.setattr("ai.interop_assistant.requests.post", fake_post)

    with pytest.raises(InvalidLLMResponseError):
        call_ollama("prompt")


def test_llm_json_that_is_not_an_object_is_rejected(monkeypatch):
    monkeypatch.setattr(
        "ai.interop_assistant.call_ollama",
        lambda prompt: ["not", "an", "object"]
    )

    with pytest.raises(InvalidLLMResponseError):
        diagnose_interop_error("erreur", "MSH|^~\\&|A|B", "blocking")
