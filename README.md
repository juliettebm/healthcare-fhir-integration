# 🏥 Healthcare FHIR Integration

[![Tests](https://github.com/juliettebm/healthcare-fhir-integration/actions/workflows/tests.yml/badge.svg)](https://github.com/juliettebm/healthcare-fhir-integration/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FHIR](https://img.shields.io/badge/FHIR-R4-orange)](https://hl7.org/fhir/R4/)
[![HL7](https://img.shields.io/badge/HL7-v2%20ADT-blue)](https://www.hl7.org/)
[![SQLite](https://img.shields.io/badge/SQL-SQLite-lightgrey?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Ollama](https://img.shields.io/badge/Ollama-Llama%203.2-black)](https://ollama.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

Healthcare interoperability mini-project in Python: consume a FHIR R4 REST API and store the validated data in SQLite, convert HL7 v2 ADT messages into FHIR `Patient` resources, and triage support requests with a guard-railed local LLM.

---

## Objective

Hospitals, imaging centres and optical or hearing-aid retailers each run their own software. Making them exchange patient data means speaking several standards and coping with data that is late, partial or malformed. This project explores three small, realistic building blocks:

1. **Consume a FHIR API**: query a REST server, walk through paginated `Bundle`s, validate and normalise `Patient` resources, persist them in SQL.
2. **Translate HL7 v2 to FHIR**: parse the `PID` segment of an ADT message and map it to a FHIR `Patient`, handling incomplete or invalid values explicitly.
3. **Use an LLM where it helps, and only there**: explain integration errors and classify support requests, while deterministic Python code keeps every decision that can be made reliably.

The goal is a small project that is fully understood and defensible, not an integration engine.

---

## Data

- **FHIR source**: the public [HAPI FHIR R4 test server](https://hapi.fhir.org/baseR4). It is a shared test environment: content changes and must never be treated as real patient data.
- **HL7 sample**: `hl7/sample_message.hl7` is a **fictional** ADT^A01 message.
- **Support requests**: `ai/support_tickets.json` contains 26 **fictional** labelled requests.
- The SQLite database (`patients.db`) and the generated `hl7/patient.json` are not versioned (see `.gitignore`).

---

## Project Structure

```
healthcare-fhir-integration/
│
├── .github/workflows/
│   └── tests.yml                  # CI: runs pytest on every push and pull request
├── ai/
│   ├── interop_assistant.py       # local LLM client (Ollama), typed errors, diagnosis validation
│   ├── ticket_triage.py           # closed-category classification of support requests
│   ├── evaluate_triage.py         # accuracy measurement on labelled requests
│   └── support_tickets.json       # 26 fictional labelled requests
├── hl7/
│   ├── hl7_to_fhir.py             # HL7 v2 PID -> FHIR Patient, dates, gender, AI fallback
│   └── sample_message.hl7         # fictional ADT^A01 message
├── src/
│   ├── fhir_client.py             # HTTP calls, timeouts, Bundle pagination
│   ├── parser.py                  # Patient normalisation and validation
│   └── database.py                # SQLite persistence (idempotent upsert)
├── tests/                         # pytest suite (parsing, mapping, HTTP errors, DB, LLM guardrails)
├── app.py                         # optional Streamlit demo of the triage
├── main.py                        # FHIR -> SQLite pipeline
├── requirements.txt
├── requirements-app.txt           # adds Streamlit (optional demo only)
├── .gitignore
├── LICENSE
└── README.md
```

---

## Reproduce

### 1. Clone the repository

```bash
git clone https://github.com/juliettebm/healthcare-fhir-integration.git
cd healthcare-fhir-integration
```

### 2. Install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the pipelines

```bash
python main.py                    # FHIR API -> validation -> SQLite (3 pages of 5 patients)
python -m hl7.hl7_to_fhir         # HL7 v2 -> FHIR Patient, written to hl7/patient.json
python -m pytest                  # test suite
```

The FHIR pipeline is deliberately capped at 3 pages to avoid overloading the public test server.

### 4. Optional: local LLM features

Install [Ollama](https://ollama.com/), then:

```bash
ollama pull llama3.2
python -m ai.evaluate_triage      # measure the support-request triage
pip install -r requirements-app.txt
streamlit run app.py              # minimal triage demo
```

Nothing in the FHIR or HL7 pipelines depends on the LLM: if Ollama is unavailable, they run unchanged.

---

## Methodology

### FHIR API to SQLite

```
FHIR R4 API -> HTTP GET -> Bundle -> pagination (link "next") -> parsing -> validation -> SQLite
```

1. **Retrieval**: `requests` with an explicit timeout and `raise_for_status()`.
2. **Pagination**: the `next` link of each `Bundle` is followed, up to a page cap.
3. **Parsing**: fields that may be absent (`name`, `gender`, `birthDate`) are read defensively; a missing field becomes `None`, never a crash.
4. **Validation**: a patient without an `id` is skipped and logged.
5. **Persistence**: `INSERT OR REPLACE` keyed on the FHIR `id`, so re-running the pipeline updates existing rows instead of duplicating them.

### HL7 v2 to FHIR

```
ADT^A01 -> PID segment -> split fields and components -> mapping -> FHIR Patient -> JSON
```

| HL7 v2 | FHIR |
| --- | --- |
| `PID-3` | `Patient.identifier` |
| `PID-5.1` | `Patient.name.family` |
| `PID-5.2` | `Patient.name.given` |
| `PID-7` | `Patient.birthDate` |
| `PID-8` | `Patient.gender` |

- **Dates**: `19920403` becomes `1992-04-03`, `199204` becomes `1992-04`, `1992` stays `1992` (FHIR `date` allows partial precision). Impossible dates such as `20260231` are rejected with a warning.
- **Gender**: `F`, `M`, `O`, `U` map to `female`, `male`, `other`, `unknown`. Any other code becomes `unknown` and raises a warning, because it loses information. An empty field is `unknown` without warning: absence of data is not an invalid value.

### Where the LLM is used

| Use | LLM's role | Python's role |
| --- | --- | --- |
| Error diagnosis | Explains a blocking HL7 error in plain language | Detects the error, **decides the severity**, validates the JSON contract |
| Request triage | Picks one category from a closed list | Rejects any answer outside the list |

The LLM is optional and isolated: an unreachable Ollama or an unusable answer is logged and the pipeline carries on. Real example, for a message with no `PID` segment:

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

## Key Results

**Tests.** The pytest suite covers FHIR parsing and missing fields, Bundle pagination, HTTP errors, SQLite persistence and idempotent upsert, HL7 mapping (complete, partial and invalid dates, unexpected gender codes, incomplete `PID`), and the LLM guardrails (Ollama down versus invalid answer, severity imposed by Python). It runs on GitHub Actions at every push.

**Support-request triage** (26 fictional labelled requests, Llama 3.2 3B, temperature 0):

| Prompt version | Correct answers |
| --- | --- |
| Baseline | **23 / 26** |
| Sharper definition of `question_de_format` | 22 / 26 |
| Extra rule in the system prompt | 20 / 26 |

---

## Methodological Notes

**Deterministic rules stay in Python.** Parsing, mapping, validation, error detection and severity are plain code. The prompt tells the model the severity and forbids re-evaluating it, and a test checks that Python's value wins over the model's.

**`PID-3` maps to `Patient.identifier`, not `Patient.id`.** The source system's business identifier is kept distinct from the logical id of the FHIR resource.

**No patient value in logs.** Warnings about invalid dates or codes describe the problem without printing the patient's data. The unexpected gender *code* is logged, since it is a code and not an identifier.

**Validation checks the contract, not the truth.** A support request such as *"A patient does not appear on our side, is it a sync problem?"* is classified as `question_de_format` because it is phrased as a question. Python cannot catch this: the category is in the allowed list. Two prompt fixes were measured (table above), each lowered the overall score, and both were reverted. With a small local model, wording moves results a lot, so changes are measured before being kept.

**The triage score is optimistic.** Requests and prompt were written by the same person on a very small set. It illustrates an evaluation method, not real-world performance.

---

## Limitations and Next Steps

- HL7 parsing is deliberately naive: only the `PID` segment of ADT messages, no custom separators, no field repetitions (`~`), no escape sequences, no dates with time or time zone.
- The assigning authority in `PID-3` (`HOSPITAL_A`) is not yet mapped to `identifier.system`.
- FHIR validation is limited to checking the resource `id`; a full validator would check profiles.
- Add other segments and message types, other FHIR resources, and sending generated resources to a FHIR server.
- Larger, harder evaluation set for the triage (ambiguous requests, anonymised real ones); abstraction of the LLM provider.
- Advanced logging (files, rotation, configurable levels).

---

## Disclaimer

⚠️ Educational prototype. It uses a public test server and fictional data only, and is not an integration engine. Running the LLM locally with Ollama keeps data on the machine but is not, by itself, a compliance or security guarantee for real health data.

---

## Stack

Python 3.12 · requests · SQLite · pytest · GitHub Actions · Ollama (Llama 3.2) · Streamlit (optional)

---

## License

Released under the [MIT License](LICENSE).

---

## Author

**Juliette Bouli-Mengue**
Clinical Research to Data Science
