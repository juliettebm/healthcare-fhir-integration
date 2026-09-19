import logging

import requests

import main


def test_fhir_api_error_is_handled(monkeypatch, caplog):
    def fake_get_patient_pages():
        raise requests.RequestException("FHIR server unavailable")

    monkeypatch.setattr(
        main,
        "get_patient_pages",
        fake_get_patient_pages
    )

    with caplog.at_level(logging.ERROR):
        main.main()

    assert "Erreur lors de l'appel à l'API FHIR" in caplog.text