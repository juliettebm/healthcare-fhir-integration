"""Mesure la qualité du tri de demandes sur des tickets fictifs étiquetés.

Usage : python -m ai.evaluate_triage
"""
import json
from pathlib import Path

from ai.interop_assistant import InvalidLLMResponseError, OllamaUnavailableError
from ai.ticket_triage import classify_ticket

TICKETS_FILE = Path(__file__).parent / "support_tickets.json"


def main():
    tickets = json.loads(TICKETS_FILE.read_text(encoding="utf-8"))

    correct = 0
    rejected = 0
    mistakes = []

    for ticket in tickets:
        try:
            predicted = classify_ticket(ticket["text"])
        except OllamaUnavailableError as error:
            print(f"Ollama indisponible, évaluation arrêtée : {error}")
            return
        except InvalidLLMResponseError:
            rejected += 1
            mistakes.append((ticket["text"], ticket["expected"], "(réponse rejetée)"))
            continue

        if predicted == ticket["expected"]:
            correct += 1
        else:
            mistakes.append((ticket["text"], ticket["expected"], predicted))

    print(f"Résultat : {correct} bonnes réponses sur {len(tickets)}")
    print(f"Réponses rejetées par la validation : {rejected}")

    for text, expected, predicted in mistakes:
        print(f"\n- {text}\n  attendu : {expected} | obtenu : {predicted}")


if __name__ == "__main__":
    main()
