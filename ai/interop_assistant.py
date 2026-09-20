import json

import requests


class OllamaUnavailableError(Exception):
    """Ollama est injoignable ou a répondu avec une erreur HTTP."""


class InvalidLLMResponseError(ValueError):
    """Ollama a répondu, mais la réponse n'est pas un diagnostic exploitable."""


SYSTEM_PROMPT = """
Tu es un assistant technique spécialisé en interopérabilité des systèmes d'information en santé.

Tu analyses des erreurs provenant d'un pipeline HL7 v2 vers FHIR.

Règles :
- N'invente jamais de donnée patient.
- Ne complète jamais une donnée HL7 absente.
- Ne modifie jamais le message HL7 source.
- Analyse uniquement les informations techniques fournies.
- Si une information est inconnue, indique qu'elle est inconnue.
- Propose uniquement des actions techniques de diagnostic ou de correction.

Ta réponse doit identifier :
- le type d'erreur ;
- l'élément HL7 concerné ;
- l'impact sur la ressource FHIR ;
- une explication technique ;
- une action technique suggérée.
"""

def build_error_context(error_message, hl7_message, severity):
    return {
        "error_message": error_message,
        "hl7_message": hl7_message,
        "severity": severity
    }

DIAGNOSTIC_SCHEMA = {
    "error_type": "",
    "severity": "",
    "hl7_element": "",
    "fhir_impact": "",
    "explanation": "",
    "suggested_action": ""
}

def validate_diagnostic(diagnostic):
    required_fields = DIAGNOSTIC_SCHEMA.keys()

    for field in required_fields:
        if field not in diagnostic:
            return False

    allowed_severities = ["warning", "error", "blocking"]

    if diagnostic["severity"] not in allowed_severities:
        return False

    return True

def build_user_prompt(context):
    return f"""
Analyse l'erreur d'interopérabilité suivante.

Erreur détectée :
{context["error_message"]}

Sévérité déterminée par le pipeline :
{context["severity"]}

Message HL7 :
{context["hl7_message"]}

Retourne uniquement un objet JSON avec exactement les champs suivants :
- error_type
- severity
- hl7_element
- fhir_impact
- explanation
- suggested_action

La sévérité est déterminée par le pipeline Python.
Tu ne dois pas la modifier ni la réévaluer.
Le champ "severity" de ta réponse doit reprendre exactement la valeur fournie.

N'ajoute aucun texte en dehors du JSON.
"""

def call_ollama(prompt, system_prompt=SYSTEM_PROMPT):
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "llama3.2",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "options": {"temperature": 0},
                "format": "json"
            },
            timeout=60
        )

        response.raise_for_status()

    except requests.RequestException as error:
        raise OllamaUnavailableError(
            f"Ollama indisponible : {error}"
        ) from error

    try:
        content = response.json()["message"]["content"]

        return json.loads(content)

    except (ValueError, KeyError, TypeError) as error:
        raise InvalidLLMResponseError(
            f"Réponse Ollama illisible : {error}"
        ) from error

def diagnose_interop_error(error_message, hl7_message, severity):
    context = build_error_context(
        error_message,
        hl7_message,
        severity
    )

    prompt = build_user_prompt(context)

    diagnostic = call_ollama(prompt)

    if not isinstance(diagnostic, dict):
        raise InvalidLLMResponseError("Diagnostic LLM invalide")

    diagnostic["severity"] = severity

    if not validate_diagnostic(diagnostic):
        raise InvalidLLMResponseError("Diagnostic LLM invalide")

    return diagnostic

