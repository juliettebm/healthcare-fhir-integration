import pytest
import requests

from src.fhir_client import (
    get_patients,
    get_next_link,
    get_patient_pages
)


def test_get_next_link():
    bundle = {
        "link": [
            {"relation": "self", "url": "https://example.org/page1"},
            {"relation": "next", "url": "https://example.org/page2"}
        ]
    }

    result = get_next_link(bundle)

    assert result == "https://example.org/page2"


def test_get_next_link_returns_none_without_next_page():
    bundle = {
        "link": [
            {"relation": "self", "url": "https://example.org/page1"}
        ]
    }

    result = get_next_link(bundle)

    assert result is None


def test_get_patients_raises_on_http_error(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            raise requests.HTTPError("500 Server Error")

        def json(self):
            return {}

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "src.fhir_client.requests.get",
        fake_get
    )

    with pytest.raises(requests.HTTPError):
        get_patients()


def test_patient_pagination(monkeypatch):
    first_bundle = {
        "resourceType": "Bundle",
        "id": "page1",
        "link": [
            {
                "relation": "next",
                "url": "https://example.org/page2"
            }
        ]
    }

    second_bundle = {
        "resourceType": "Bundle",
        "id": "page2",
        "link": []
    }

    monkeypatch.setattr(
        "src.fhir_client.get_patients",
        lambda: first_bundle
    )

    monkeypatch.setattr(
        "src.fhir_client.get_page",
        lambda url: second_bundle
    )

    pages = list(get_patient_pages())

    assert len(pages) == 2
    assert pages[0]["id"] == "page1"
    assert pages[1]["id"] == "page2"