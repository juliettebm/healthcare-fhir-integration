import requests

import main


def test_fhir_api_error_is_handled(monkeypatch, capsys):
    def fake_get_patient_pages():
        raise requests.RequestException("FHIR server unavailable")

    monkeypatch.setattr(
        main,
        "get_patient_pages",
        fake_get_patient_pages
    )

    main.main()

    captured = capsys.readouterr()

    assert "Erreur lors de l'appel à l'API FHIR" in captured.out