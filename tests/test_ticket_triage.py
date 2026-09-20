import pytest

from ai.interop_assistant import InvalidLLMResponseError
from ai.ticket_triage import CATEGORIES, build_triage_prompt, classify_ticket


def test_classify_ticket_returns_known_category(monkeypatch):
    monkeypatch.setattr(
        "ai.ticket_triage.call_ollama",
        lambda prompt, system_prompt: {"category": "donnee_manquante"}
    )

    assert classify_ticket("La date de naissance est vide") == "donnee_manquante"


def test_classify_ticket_rejects_unknown_category(monkeypatch):
    monkeypatch.setattr(
        "ai.ticket_triage.call_ollama",
        lambda prompt, system_prompt: {"category": "urgence_absolue"}
    )

    with pytest.raises(InvalidLLMResponseError):
        classify_ticket("Une demande")


@pytest.mark.parametrize(
    "bad_response",
    [{}, {"category": None}, ["donnee_manquante"]]
)
def test_classify_ticket_rejects_malformed_response(monkeypatch, bad_response):
    monkeypatch.setattr(
        "ai.ticket_triage.call_ollama",
        lambda prompt, system_prompt: bad_response
    )

    with pytest.raises(InvalidLLMResponseError):
        classify_ticket("Une demande")


def test_triage_prompt_lists_every_category():
    prompt = build_triage_prompt("Une demande")

    for category in CATEGORIES:
        assert category in prompt
