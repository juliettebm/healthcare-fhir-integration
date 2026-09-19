from ai.interop_assistant import (
    validate_diagnostic,
    build_error_context,
    diagnose_interop_error
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