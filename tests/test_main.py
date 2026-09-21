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

def test_main_never_prints_patient_values(monkeypatch, capsys):
    """Les valeurs patient ne doivent apparaître ni dans stdout ni dans les logs."""
    bundle = {"entry": [{"resource": {
        "resourceType": "Patient", "id": "PAT-SECRET",
        "name": [{"family": "NomSecret", "given": ["PrenomSecret"]}],
    }}]}
    monkeypatch.setattr(main, "get_patient_pages", lambda: [bundle])
    monkeypatch.setattr(main, "create_database", lambda: None)
    monkeypatch.setattr(main, "save_patients", lambda patients: None)
    monkeypatch.setattr(main, "get_all_patients", lambda: [("PAT-SECRET", "PrenomSecret", "NomSecret")])

    main.main()

    output = capsys.readouterr().out
    for secret in ("NomSecret", "PrenomSecret", "PAT-SECRET"):
        assert secret not in output
