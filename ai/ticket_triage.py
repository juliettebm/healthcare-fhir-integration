"""Tri de demandes de support d'interopérabilité par un LLM sous garde-fous.

Le LLM choisit une catégorie dans une liste fermée (`CATEGORIES`) ; toute
réponse hors de cette liste est rejetée par Python. Le modèle classe la
demande, il n'y répond jamais.

Outils : Ollama (Llama 3.2 3B, température 0) via ai/interop_assistant.py.
Évaluation sur 26 tickets fictifs étiquetés : voir ai/evaluate_triage.py.
"""
from ai.interop_assistant import InvalidLLMResponseError, call_ollama

CATEGORIES = {
    "erreur_de_mapping": "une valeur est mal convertie ou associée au mauvais champ entre deux formats",
    "donnee_manquante": "un champ ou un enregistrement est vide, absent ou incomplet",
    "probleme_de_connexion": "les échanges avec un système sont coupés, lents ou en erreur (timeout, 500...)",
    "question_de_format": "question sur la structure d'un standard (HL7, FHIR, JSON) ou sur sa documentation",
    "autre": "ne correspond à aucune autre catégorie",
}

TRIAGE_SYSTEM_PROMPT = """
Tu es un assistant de tri de demandes de support technique en interopérabilité en santé.
Tu classes chaque demande dans exactement une catégorie de la liste fournie.
Tu ne réponds jamais à la demande elle-même.
"""


def build_triage_prompt(ticket_text):
    categories = "\n".join(
        f"- {name} : {description}" for name, description in CATEGORIES.items()
    )

    return f"""
Classe la demande suivante dans exactement une de ces catégories :
{categories}

Demande :
{ticket_text}

Retourne uniquement un objet JSON de la forme {{"category": "<nom de la catégorie>"}}.
"""


def classify_ticket(ticket_text):
    response = call_ollama(
        build_triage_prompt(ticket_text),
        system_prompt=TRIAGE_SYSTEM_PROMPT,
    )

    if not isinstance(response, dict):
        raise InvalidLLMResponseError("Réponse de tri invalide")

    category = response.get("category")

    if category not in CATEGORIES:
        raise InvalidLLMResponseError(f"Catégorie inconnue : {category!r}")

    return category
