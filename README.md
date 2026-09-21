# 🏥 Healthcare FHIR Integration

[![Tests](https://github.com/juliettebm/healthcare-fhir-integration/actions/workflows/tests.yml/badge.svg)](https://github.com/juliettebm/healthcare-fhir-integration/actions/workflows/tests.yml)
[![Reproducibility](https://img.shields.io/badge/reproducibility-pinned%20%2B%20tested-success)](requirements.txt)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FHIR](https://img.shields.io/badge/FHIR-R4-orange)](https://hl7.org/fhir/R4/)
[![HL7](https://img.shields.io/badge/HL7-v2%20ADT-blue)](https://www.hl7.org/)
[![SQLite](https://img.shields.io/badge/SQL-SQLite-lightgrey?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Ollama](https://img.shields.io/badge/Ollama-Llama%203.2-black)](https://ollama.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

Mini-projet d'interopérabilité en santé en Python : consommer une API REST FHIR R4 et stocker les données validées dans SQLite, convertir des messages HL7 v2 ADT en ressources FHIR `Patient`, et trier des demandes de support avec un LLM local sous garde-fous.

---

## Objectif

Les hôpitaux, les centres d'imagerie ou les opticiens et audioprothésistes utilisent chacun leur propre logiciel. Les faire échanger des données patient impose de parler plusieurs standards et de composer avec des données en retard, partielles ou mal formées. Ce projet explore trois briques réalistes et de petite taille :

1. **Consommer une API FHIR** : interroger un serveur REST, parcourir les `Bundle` paginés, valider et normaliser les ressources `Patient`, les stocker en SQL.
2. **Traduire du HL7 v2 en FHIR** : lire le segment `PID` d'un message ADT et le convertir en `Patient` FHIR, en traitant explicitement les valeurs incomplètes ou invalides.
3. **Utiliser un LLM là où il aide, et seulement là** : expliquer les erreurs d'intégration et classer des demandes de support, tandis que le code Python garde toutes les décisions qui peuvent être prises de façon fiable.

Ce projet est un démonstrateur éducatif construit sur des données publiques et fictives, qui reflète les missions d'un poste d'interopérabilité en santé, où des connecteurs relient des logiciels hospitaliers à des applications modernes : comprendre des formats hétérogènes (HL7 v2, FHIR, JSON), fiabiliser les flux de données, rendre les erreurs techniques exploitables par une équipe de support, et documenter l'ensemble. Stack : Python, API REST (`requests`), FHIR R4, HL7 v2, SQLite, pytest et GitHub Actions, plus un LLM local (Ollama, Llama 3.2) utilisé uniquement comme assistant optionnel.

Le but est un petit projet entièrement compris et défendable, pas un moteur d'intégration. Il n'est ni validé pour un usage clinique ou de production, ni destiné à manipuler de vraies données patient.

---

## Jeu de données

- **Source FHIR** : le [serveur de test public HAPI FHIR R4](https://hapi.fhir.org/baseR4). C'est un environnement de test partagé : son contenu change et ne doit jamais être traité comme de vraies données patient.
- **Exemple HL7** : `hl7/sample_message.hl7` est un message ADT^A01 **fictif**.
- **Demandes de support** : `ai/support_tickets.json` contient 26 demandes étiquetées **fictives**.
- La base SQLite (`patients.db`) et le fichier généré `hl7/patient.json` ne sont pas versionnés (voir `.gitignore`).

---

## Structure du projet

```
healthcare-fhir-integration/
│
├── .github/workflows/
│   └── tests.yml                  # CI : lance pytest à chaque push et pull request
├── ai/
│   ├── interop_assistant.py       # client LLM local (Ollama), erreurs typées, validation du diagnostic
│   ├── ticket_triage.py           # classification des demandes de support en catégories fermées
│   ├── evaluate_triage.py         # mesure de l'exactitude sur des demandes étiquetées
│   ├── triage_results.json        # métriques versionnées utilisées par le test de contrat du README
│   └── support_tickets.json       # 26 demandes fictives étiquetées
├── hl7/
│   ├── hl7_to_fhir.py             # HL7 v2 PID -> FHIR Patient, dates, genre, diagnostic IA de repli
│   └── sample_message.hl7         # message ADT^A01 fictif
├── notebooks/
│   ├── 01_fhir_to_sqlite.ipynb    # lecture et persistance FHIR documentées, hors ligne
│   ├── 02_hl7_to_fhir.ipynb       # mapping HL7 PID -> FHIR Patient et cas limites
│   └── 03_llm_triage_evaluation.ipynb # métriques de triage versionnées et décisions
├── src/
│   ├── fhir_client.py             # appels HTTP, délais maximum, pagination des Bundle
│   ├── parser.py                  # normalisation et validation des Patient
│   └── database.py                # persistance SQLite (pas de doublon au relancement)
├── tests/                         # suite pytest (parsing, mapping, erreurs HTTP, base, garde-fous LLM)
├── app.py                         # démo Streamlit optionnelle du triage
├── main.py                        # pipeline FHIR -> SQLite
├── requirements.txt
├── requirements-app.txt           # ajoute Streamlit (démo optionnelle uniquement)
├── .python-version                # version exacte de l'interpréteur utilisée en CI
├── .gitignore
├── LICENSE
└── README.md
```

---

## Reproduire

### 1. Cloner le dépôt

```bash
git clone https://github.com/juliettebm/healthcare-fhir-integration.git
cd healthcare-fhir-integration
```

### 2. Installer les dépendances

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS : source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Lancer les pipelines

```bash
python main.py                    # API FHIR -> validation -> SQLite (3 pages de 5 patients)
python -m hl7.hl7_to_fhir         # HL7 v2 -> FHIR Patient, écrit dans hl7/patient.json
python -m pytest                  # suite de tests
```

Le pipeline FHIR est volontairement limité à 3 pages pour ne pas surcharger le serveur de test public.

Les notebooks s'exécutent dans l'ordre numérique. Ils utilisent des exemples locaux fictifs ou versionnés et importent les modules de production au lieu de dupliquer leur implémentation ; le premier notebook évite volontairement d'appeler le serveur FHIR public, dont le contenu change.

### 4. Optionnel : fonctions LLM locales

Installer [Ollama](https://ollama.com/), puis :

```bash
ollama pull llama3.2
python -m ai.evaluate_triage      # mesurer le tri des demandes de support
pip install -r requirements-app.txt
streamlit run app.py              # démo minimale du triage
```

Rien dans les pipelines FHIR ou HL7 ne dépend du LLM : si Ollama est indisponible, ils fonctionnent à l'identique.

---

## Méthodologie

### De l'API FHIR à SQLite

```
API FHIR R4 -> HTTP GET -> Bundle -> pagination (lien "next") -> parsing -> validation -> SQLite
```

1. **Récupération** : `requests` avec un délai maximum explicite et `raise_for_status()`.
2. **Pagination** : le lien `next` de chaque `Bundle` est suivi, jusqu'à un plafond de pages.
3. **Parsing** : les champs pouvant être absents (`name`, `gender`, `birthDate`) sont lus de façon défensive ; un champ manquant devient `None`, jamais une erreur.
4. **Validation** : un patient sans `id` est ignoré et journalisé.
5. **Persistance** : `INSERT OR REPLACE` sur l'`id` FHIR, si bien que relancer le pipeline met à jour les lignes existantes au lieu de les dupliquer.

### De HL7 v2 à FHIR

```
ADT^A01 -> segment PID -> découpage champs et composants -> mapping -> FHIR Patient -> JSON
```

| HL7 v2 | FHIR |
| --- | --- |
| `PID-3` | `Patient.identifier` |
| `PID-5.1` | `Patient.name.family` |
| `PID-5.2` | `Patient.name.given` |
| `PID-7` | `Patient.birthDate` |
| `PID-8` | `Patient.gender` |

- **Dates** : `19920403` devient `1992-04-03`, `199204` devient `1992-04`, `1992` reste `1992` (le type FHIR `date` accepte une précision partielle). Les dates impossibles comme `20260231` sont rejetées avec un avertissement et la clé `birthDate` est alors omise de la ressource : une propriété nulle n'est pas valide en FHIR.
- **Genre** : `F`, `M`, `O`, `U` correspondent à `female`, `male`, `other`, `unknown`. Tout autre code devient `unknown` et déclenche un avertissement, car il fait perdre de l'information. Un champ vide donne `unknown` sans avertissement : l'absence de donnée n'est pas une valeur invalide.

### Où le LLM intervient

| Usage | Rôle du LLM | Rôle de Python |
| --- | --- | --- |
| Diagnostic d'erreur | Explique en langage clair une erreur HL7 bloquante | Détecte l'erreur, **décide de la sévérité**, valide le contrat JSON |
| Tri des demandes | Choisit une catégorie dans une liste fermée | Rejette toute réponse hors de la liste |

Le LLM est optionnel et isolé : si Ollama est injoignable ou si la réponse est inexploitable, l'incident est journalisé et le pipeline continue. Exemple réel, pour un message sans segment `PID` :

```json
{
  "error_type": "Segment manquant",
  "severity": "blocking",
  "hl7_element": "PID",
  "fhir_impact": "Ressource FHIR non créée",
  "explanation": "Le segment PID est essentiel pour identifier le patient dans le message HL7.",
  "suggested_action": "Vérifier que le segment PID est correctement envoyé dans le message HL7."
}
```

---

## Résultats clés

**Tests.** La suite pytest couvre le parsing FHIR et les champs manquants, la pagination des Bundle, les erreurs HTTP, la persistance SQLite et l'absence de doublon quand on relance l'import, le mapping HL7 (dates complètes, partielles et invalides, codes de genre inattendus, `PID` incomplet) et les garde-fous du LLM (Ollama arrêté ou réponse invalide, sévérité imposée par Python). Elle s'exécute sur GitHub Actions à chaque push.

**Tri des demandes de support** (26 demandes fictives étiquetées, Llama 3.2 3B, température 0). L'intervalle quantifie l'incertitude d'échantillonnage sur ce petit jeu interne ; il ne tient pas compte de la variabilité du LLM d'une exécution à l'autre :

| Version du prompt | Réponses correctes | Exactitude (IC de Wilson à 95 %) |
| --- | --- | --- |
| Référence | **23 / 26** | 88.5% (71.0%–96.0%) |
| Définition plus précise de question_de_format | **22 / 26** | 84.6% (66.5%–93.8%) |
| Règle supplémentaire dans le prompt système | **20 / 26** | 76.9% (57.9%–89.0%) |

La source lisible par machine est `ai/triage_results.json`. Un test pytest vérifie le nombre de demandes, recalcule chaque intervalle et contrôle que ce tableau n'a pas divergé des résultats versionnés.

---

## Notes méthodologiques

**Les règles déterministes restent dans Python.** Le parsing, le mapping, la validation, la détection d'erreur et la sévérité sont du code ordinaire. Le prompt indique la sévérité au modèle et lui interdit de la réévaluer, et un test vérifie que la valeur de Python l'emporte sur celle du modèle.

**`PID-3` correspond à `Patient.identifier`, pas à `Patient.id`.** L'identifiant métier du système source reste distinct de l'identifiant logique de la ressource FHIR.

**Aucune valeur patient dans les logs.** Les avertissements sur une date ou un code invalide décrivent le problème sans afficher les données du patient. Le *code* de genre inattendu est journalisé, car c'est un code et non un identifiant.

**La validation vérifie le contrat, pas la vérité.** Une demande comme *« Un patient n'apparaît pas chez nous, est-ce un problème de synchronisation ? »* est classée `question_de_format` parce qu'elle est formulée comme une question. Python ne peut pas l'intercepter : la catégorie figure dans la liste autorisée. Deux corrections de prompt ont été mesurées (tableau ci-dessus) ; chacune a fait baisser le score global et les deux ont été annulées. Avec un petit modèle local, la formulation fait beaucoup varier les résultats, donc les changements sont mesurés avant d'être conservés.

**Le score de triage est optimiste.** Les demandes et le prompt ont été écrits par la même personne sur un très petit jeu. Il illustre une méthode d'évaluation, pas une performance en conditions réelles.

**La calibration n'est pas rapportée.** Ce classifieur LLM renvoie une catégorie validée, pas une probabilité stable. Une courbe de calibration ou un score de Brier serait donc trompeur ; la calibration ne devient pertinente que si l'interface expose des probabilités de classe reproductibles.

---

## Limites et prochaines étapes

- Le parsing HL7 est volontairement simple : uniquement le segment `PID` des messages ADT, pas de séparateurs personnalisés, pas de répétitions de champs (`~`), pas de séquences d'échappement, pas de dates avec heure ou fuseau horaire.
- L'autorité d'affectation de `PID-3` (`HOSPITAL_A`) n'est pas encore mappée vers `identifier.system`.
- La validation FHIR se limite au contrôle de l'`id` de la ressource ; un validateur complet vérifierait les profils.
- Ajouter d'autres segments et types de messages, d'autres ressources FHIR, et l'envoi des ressources générées vers un serveur FHIR.
- Jeu d'évaluation plus grand et plus difficile pour le triage (demandes ambiguës, demandes réelles anonymisées) ; abstraction du fournisseur de LLM.
- Journalisation avancée (fichiers, rotation, niveaux configurables).

---

## Avertissement

⚠️ Prototype éducatif. Il utilise un serveur de test public et des données fictives uniquement, et n'est pas un moteur d'intégration. Exécuter le LLM en local avec Ollama garde les données sur la machine, mais ne constitue pas en soi une garantie de conformité ou de sécurité pour de vraies données de santé.

---

## Stack

Python 3.12 · requests · SQLite · pytest · GitHub Actions · Ollama (Llama 3.2) · Streamlit (optionnel)

---

## Licence

Publié sous [licence MIT](LICENSE).

---

## Autrice

**Juliette Bouli-Mengue**
De la recherche clinique à la data science
