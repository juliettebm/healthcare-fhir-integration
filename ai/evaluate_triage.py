"""Mesure la qualité du tri de demandes sur des tickets fictifs étiquetés.

Usage : python -m ai.evaluate_triage
"""
import json
import math
from pathlib import Path

from ai.interop_assistant import InvalidLLMResponseError, OllamaUnavailableError
from ai.ticket_triage import classify_ticket

TICKETS_FILE = Path(__file__).parent / "support_tickets.json"


def wilson_interval(correct: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Return a Wilson score interval without adding a statistics dependency."""
    if total <= 0:
        raise ValueError("total must be positive")
    if not 0 <= correct <= total:
        raise ValueError("correct must be between zero and total")

    proportion = correct / total
    denominator = 1 + z**2 / total
    centre = (proportion + z**2 / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt(proportion * (1 - proportion) / total + z**2 / (4 * total**2))
        / denominator
    )
    return centre - margin, centre + margin


def evaluate(tickets):
    """Classe chaque ticket et renvoie le nombre de bonnes réponses, de rejets et la liste des erreurs.

    Lève OllamaUnavailableError si Ollama ne répond pas.
    """
    correct = 0
    rejected = 0
    mistakes = []

    for ticket in tickets:
        try:
            predicted = classify_ticket(ticket["text"])
        except InvalidLLMResponseError:
            rejected += 1
            mistakes.append((ticket["text"], ticket["expected"], "(réponse rejetée)"))
            continue

        if predicted == ticket["expected"]:
            correct += 1
        else:
            mistakes.append((ticket["text"], ticket["expected"], predicted))

    return {"correct": correct, "rejected": rejected, "mistakes": mistakes}


def print_report(outcome, total):
    correct = outcome["correct"]
    print(f"Résultat : {correct} bonnes réponses sur {total}")
    lower, upper = wilson_interval(correct, total)
    print(f"Exactitude : {correct / total:.1%} (IC 95 % de Wilson : {lower:.1%}–{upper:.1%})")
    print(f"Réponses rejetées par la validation : {outcome['rejected']}")

    for text, expected, predicted in outcome["mistakes"]:
        print(f"\n- {text}\n  attendu : {expected} | obtenu : {predicted}")


def main():
    tickets = json.loads(TICKETS_FILE.read_text(encoding="utf-8"))

    try:
        outcome = evaluate(tickets)
    except OllamaUnavailableError as error:
        print(f"Ollama indisponible, évaluation arrêtée : {error}")
        return

    print_report(outcome, len(tickets))


if __name__ == "__main__":
    main()
