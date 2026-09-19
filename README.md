# Healthcare FHIR Integration

Mini projet d'interopérabilité en santé développé en Python, autour des standards FHIR R4 et HL7 v2.

L'objectif est d'explorer trois scénarios d'interopérabilité en santé :

1. Consommer des ressources `Patient` depuis une API REST FHIR, les normaliser, les valider et les stocker localement.
2. Transformer les données patient d'un message HL7 v2 ADT en une ressource FHIR `Patient` au format JSON.
3. Assister le diagnostic d'erreurs d'interopérabilité avec un LLM local, tout en conservant les règles critiques dans le code Python.

## Architecture

### FHIR API pipeline

```text
FHIR R4 API
     ↓
REST / HTTP
     ↓
FHIR Bundle
     ↓
Pagination
     ↓
Parsing & normalisation
     ↓
Validation
     ↓
SQLite
```

### HL7 v2 → FHIR pipeline

```text
HL7 v2 ADT^A01
       ↓
Extraction du segment PID
       ↓
Parsing des champs et composants
       ↓
Mapping des données
       ↓
FHIR Patient
       ↓
JSON
```

### AI-assisted interoperability

Lorsqu'une erreur bloquante est détectée pendant le traitement HL7, le pipeline peut solliciter un assistant IA local pour produire un diagnostic technique structuré.

```text
HL7 v2 message
       ↓
Python parser
       ↓
Validation
    ↙       ↘
 valid     error
   ↓         ↓
 FHIR     Python determines severity
             ↓
        Ollama / Llama 3.2
             ↓
        Technical diagnosis
             ↓
         JSON validation
```

Le LLM n'est pas utilisé pour valider les données ni pour effectuer le mapping HL7 → FHIR. Ces opérations restent déterministes.

L'assistant IA intervient uniquement après la détection d'une erreur afin de :

- expliquer le problème technique ;
- identifier l'élément HL7 concerné ;
- décrire l'impact sur la ressource FHIR ;
- suggérer une action de diagnostic.

Les décisions déterministes, comme la sévérité d'une erreur bloquant le pipeline, restent contrôlées par le code Python.

L'assistant IA est un composant optionnel. Son indisponibilité (serveur Ollama arrêté, timeout ou réponse invalide) n'interrompt pas le pipeline principal : l'erreur d'interopérabilité détectée par Python reste disponible et le traitement HL7/FHIR fonctionne indépendamment du LLM.

## Fonctionnalités

- Consommation d'une API REST FHIR R4
- Lecture de ressources `Patient` dans des `Bundle` FHIR
- Gestion de la pagination FHIR
- Gestion des erreurs HTTP et timeout
- Normalisation et validation des données Patient
- Persistance locale avec SQLite
- Parsing d'un message HL7 v2 ADT
- Extraction et interprétation du segment PID
- Mapping HL7 v2 → FHIR Patient
- Gestion de données HL7 incomplètes
- Validation des dates HL7
- Mapping des codes de sexe HL7 vers FHIR
- Génération d'une ressource FHIR au format JSON
- Tests automatisés avec pytest
- Exécution automatique des tests avec GitHub Actions
- Assistant IA local avec Ollama et Llama 3.2
- Diagnostic assisté des erreurs d'interopérabilité HL7
- Prompt système avec garde-fous contre l'invention de données patient
- Sortie LLM structurée au format JSON
- Validation déterministe des réponses du LLM
- Séparation entre règles métier déterministes et analyse assistée par LLM
- Fallback permettant au pipeline de fonctionner lorsque l'assistant IA est indisponible

## Installation

Cloner le dépôt puis se placer dans le dossier du projet.

Créer un environnement virtuel :

```bash
python -m venv .venv
```

Activer l'environnement sous Windows :

```bash
.venv\Scripts\activate
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

### Assistant IA local

La fonctionnalité de diagnostic assisté utilise Ollama pour exécuter le modèle Llama 3.2 localement.

Après avoir installé Ollama, télécharger le modèle :

```bash
ollama pull llama3.2
```

Vérifier que le modèle est disponible :

```bash
ollama list
```

L'API locale Ollama est utilisée par l'application à l'adresse `http://localhost:11434`.

L'installation d'Ollama est optionnelle pour le fonctionnement du pipeline HL7/FHIR. Elle est uniquement nécessaire pour bénéficier du diagnostic IA enrichi.

## Utilisation

### 1. Pipeline API FHIR

Le pipeline interroge le serveur public de test HAPI FHIR R4, récupère des ressources `Patient`, gère la pagination, normalise les données puis les stocke dans une base SQLite locale.

```bash
python main.py
```

Le nombre de pages récupérées est volontairement limité afin de ne pas solliciter inutilement le serveur public de test.

> Le serveur HAPI FHIR utilisé est un environnement public de test. Son contenu peut évoluer et ne doit pas être considéré comme une source de données patient réelle.

### 2. Conversion HL7 v2 → FHIR

Un message HL7 v2 fictif est disponible dans :

```text
hl7/sample_message.hl7
```

Exécuter la conversion depuis la racine du projet :

```bash
python -m hl7.hl7_to_fhir
```

Le programme suit le pipeline suivant :

```text
sample_message.hl7
        ↓
lecture du message
        ↓
détection du segment PID
        ↓
parsing des champs HL7
        ↓
mapping HL7 → FHIR
        ↓
patient.json
```

Exemple de mapping réalisé :

| HL7 v2 | FHIR |
|---|---|
| PID-3 | Patient.identifier |
| PID-5.1 | Patient.name.family |
| PID-5.2 | Patient.name.given |
| PID-7 | Patient.birthDate |
| PID-8 | Patient.gender |

Par exemple, la valeur HL7 :

```text
19920403
```

est transformée en :

```text
1992-04-03
```

et :

```text
F
```

est mappée vers :

```text
female
```

Les dates calendaires invalides sont rejetées lors de la conversion. Les codes de sexe HL7 explicitement pris en charge sont `F`, `M`, `O` et `U`. Dans ce prototype, une autre valeur est normalisée vers `unknown`.

### 3. Diagnostic IA des erreurs d'interopérabilité

Lorsqu'une erreur bloquante est détectée pendant la conversion HL7 v2 → FHIR, le pipeline peut transmettre le contexte technique à un assistant IA local exécuté avec Ollama et Llama 3.2.

Exécuter le même pipeline :

```bash
python -m hl7.hl7_to_fhir
```

Avec un message HL7 valide, la ressource FHIR est générée normalement et le LLM n'est pas appelé.

En cas d'erreur bloquante, Python détecte d'abord l'erreur et détermine sa sévérité. Si l'assistant IA est disponible, il produit ensuite un diagnostic structuré, par exemple :

```json
{
  "error_type": "Segment manquant",
  "severity": "blocking",
  "hl7_element": "PID",
  "fhir_impact": "Ressource FHIR non créée",
  "explanation": "Le segment PID est absent dans le message HL7.",
  "suggested_action": "Vérifier que le segment PID est présent dans le message HL7 source."
}
```

La sévérité est déterminée par le pipeline Python et non par le LLM. La réponse générée est ensuite validée avant d'être utilisée par l'application.

Si l'assistant IA est indisponible ou produit une réponse ne respectant pas le contrat attendu, l'erreur détectée par Python reste disponible et le pipeline principal continue de fonctionner indépendamment du LLM.

## Tests

Lancer l'ensemble des tests :

```bash
python -m pytest
```

Le projet comporte actuellement **28 tests automatisés**.

Les tests couvrent notamment :

- le parsing et la validation de ressources FHIR Patient ;
- les champs FHIR manquants ;
- la pagination des `Bundle` FHIR ;
- l'extraction du lien `next` ;
- la gestion des erreurs HTTP de l'API FHIR ;
- la gestion d'une erreur de connexion FHIR par le programme principal ;
- la création et la persistance de patients dans une base SQLite temporaire ;
- la conversion et la validation des dates HL7 ;
- le mapping du sexe HL7 → FHIR ;
- le comportement face à un code de sexe inattendu ;
- la conversion d'un segment PID complet ;
- l'absence de prénom ;
- les segments PID incomplets ;
- l'absence de segment PID dans un message HL7 ;
- la validation de la structure des diagnostics IA ;
- le rejet des valeurs de sévérité invalides ;
- la transmission de la sévérité déterminée par le pipeline ;
- la priorité des règles déterministes Python sur les sorties du LLM ;
- le rejet d'une réponse LLM incomplète ;
- la résilience du pipeline lorsque l'assistant IA est indisponible.

Les tests du comportement IA utilisent des réponses simulées lorsque nécessaire afin de tester la logique applicative sans dépendre de la disponibilité d'un serveur Ollama.

## Intégration continue

Une workflow GitHub Actions exécute automatiquement la suite de tests lors des `push` et des pull requests.

La CI :

1. récupère le dépôt ;
2. configure Python 3.12 ;
3. installe les dépendances définies dans `requirements.txt` ;
4. exécute `python -m pytest`.

Cela permet de vérifier automatiquement que les pipelines FHIR, HL7, SQLite et la logique d'intégration IA restent fonctionnels après une modification du code.

## Structure du projet

```text
healthcare-fhir-integration/
├── .github/
│   └── workflows/
│       └── tests.yml
│
├── ai/
│   └── interop_assistant.py
│
├── hl7/
│   ├── sample_message.hl7
│   └── hl7_to_fhir.py
│
├── src/
│   ├── database.py
│   ├── fhir_client.py
│   └── parser.py
│
├── tests/
│   ├── test_database.py
│   ├── test_fhir_client.py
│   ├── test_hl7_to_fhir.py
│   ├── test_interop_assistant.py
│   ├── test_main.py
│   └── test_parser.py
│
├── .gitignore
├── main.py
└── requirements.txt
```

### Rôle des principaux modules

- `fhir_client.py` : appels HTTP vers l'API FHIR et gestion de la pagination.
- `parser.py` : normalisation et validation des ressources FHIR Patient.
- `database.py` : persistance des données normalisées dans SQLite, avec possibilité d'utiliser une base temporaire pour les tests.
- `hl7_to_fhir.py` : lecture d'un message HL7 v2, parsing du segment PID et mapping vers une ressource FHIR Patient.
- `sample_message.hl7` : message HL7 v2 fictif utilisé pour la démonstration.
- `interop_assistant.py` : assistant IA local de diagnostic des erreurs d'interopérabilité, utilisant Ollama/Llama 3.2 avec sortie JSON structurée et validation déterministe.
- `tests/` : tests automatisés des fonctions de parsing, validation, mapping, persistance et résilience.
- `.github/workflows/tests.yml` : workflow d'intégration continue exécutant automatiquement la suite pytest.

## Choix techniques

### FHIR R4

Le projet utilise des ressources `Patient` et des `Bundle` FHIR R4 afin d'expérimenter la consommation d'une API de données de santé structurées.

### HL7 v2

La partie HL7 se concentre volontairement sur un message ADT et son segment `PID`. Le parser extrait plusieurs informations patient puis les transforme vers une représentation FHIR structurée.

L'identifiant provenant de `PID-3` est mappé vers `Patient.identifier` et non vers `Patient.id`, afin de distinguer l'identifiant métier provenant du système source de l'identifiant logique d'une ressource FHIR.

Le parser HL7 de ce prototype est volontairement minimal. Il est conçu pour le message de démonstration et les séparateurs HL7 standards utilisés par le projet. Il ne constitue pas une implémentation complète du standard HL7 v2 : les répétitions, séquences d'échappement et variations avancées de séparateurs ne sont notamment pas prises en charge.

Le mapping actuel de `PID-3` conserve l'identifiant patient mais ne transforme pas encore l'assigning authority en `identifier.system`.

### Python

Le projet utilise principalement :

- `requests` pour les appels HTTP ;
- `sqlite3` pour la persistance locale ;
- `json` pour la génération de ressources FHIR JSON ;
- `pytest` pour les tests automatisés.

### Ollama et Llama 3.2

L'assistant de diagnostic utilise Llama 3.2 exécuté localement avec Ollama.

Le LLM est volontairement limité aux tâches nécessitant une interprétation en langage naturel : explication d'une erreur d'interopérabilité, description de son impact et suggestion d'une action technique.

Les opérations critiques et déterministes restent gérées par Python :

- parsing du message HL7 ;
- mapping HL7 → FHIR ;
- validation des données ;
- détection des erreurs ;
- attribution de la sévérité.

Cette séparation permet d'éviter de déléguer au LLM des décisions pouvant être déterminées de manière fiable par le code.

Les réponses du modèle sont demandées au format JSON puis validées par l'application avant utilisation. Le pipeline peut ainsi refuser une sortie qui ne respecte pas le contrat attendu.

L'assistant IA constitue une couche optionnelle d'aide au diagnostic. Une indisponibilité d'Ollama ou une réponse invalide du modèle ne doit pas interrompre le pipeline principal.

L'exécution locale via Ollama permet également de tester l'intégration d'un LLM sans dépendre d'une API externe. Ce choix ne constitue cependant pas, à lui seul, une garantie de conformité ou de sécurité pour le traitement de données de santé réelles.

## Limites et pistes d'amélioration

Ce projet est un prototype pédagogique et ne constitue pas un moteur d'intégration hospitalier complet.

Il pourrait être étendu avec :

- la prise en charge d'autres segments et types de messages HL7 v2 ;
- la gestion complète des séparateurs, répétitions et séquences d'échappement HL7 ;
- le mapping vers d'autres ressources FHIR ;
- une validation FHIR plus complète ;
- la gestion de systèmes d'identifiants (`identifier.system`) ;
- l'envoi des ressources générées vers une API FHIR ;
- une gestion plus avancée des erreurs et des logs ;
- l'utilisation d'un schéma JSON plus strict pour valider les sorties du LLM ;
- l'évaluation du comportement de l'assistant sur un jeu de cas d'erreurs HL7 ;
- la prise en charge de plusieurs catégories d'erreurs avec des niveaux de sévérité déterminés par le pipeline ;
- l'abstraction du fournisseur LLM afin de pouvoir remplacer Ollama par un autre modèle ou une API sans modifier la logique métier.

## Objectif

Ce projet a été réalisé afin de mettre en pratique les principes d'interopérabilité des systèmes d'information en santé à travers un pipeline simple et reproductible combinant Python, REST, JSON, HL7 v2 et FHIR R4, complété par un assistant IA local optionnel pour l'aide au diagnostic technique.