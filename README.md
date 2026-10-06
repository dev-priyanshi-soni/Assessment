# Marlabs GenAI Spring Boot + Python Assessment

Two-service implementation for the supplied employee policy/reimbursement assessment.

## Architecture

Client -> Spring Boot :8080 -> Python FastAPI :8000

Spring Boot:
- public `/answer` endpoint
- caller/date/request validation
- forwards trusted caller identity to Python
- public response boundary

Python:
- policy corpus
- metadata filtering
- FAISS local semantic candidate retrieval
- document TXT/PDF extraction
- deterministic offline model double
- LangGraph answer workflow
- batch processing and duplicate detection

## Important assessment rules implemented

- Caller identity comes from `X-Caller-Id`, not document text.
- Only Approved policies matching tenant, role, and effective date are eligible.
- Simultaneously applicable contradictory policies return `CONFLICT`; no precedence rule is invented.
- Missing/ambiguous request fields remain visible.
- Submitted requests are not policy sources.
- Every request requires human review.
- Exact duplicate files are detected by SHA-256.
- One item failure does not stop independent batch items.
- Offline mode does not require a paid model/API key.

## Python setup

```powershell
cd python-service
py -3.12 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Spring Boot setup

Use Java 21. From `spring-boot-service`:

```powershell
.\mvnw.cmd test
.\mvnw.cmd spring-boot:run
```

If Maven Wrapper is not present in this directory, copy `mvnw`, `mvnw.cmd`, and `.mvn/wrapper` from the Spring Initializr project you generated, or use Maven directly.

## Test Python service

```powershell
cd python-service
pytest
```

## Example

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8080/answer" `
  -Headers @{ "X-Caller-Id" = "atlas-employee-01" } `
  -ContentType "application/json" `
  -Body (@{
    question = "What is my annual certification reimbursement limit?"
    as_of = "2026-09-21"
  } | ConvertTo-Json -Compress)
```

## Data

`data/policies.json` contains the 12 supplied policy passages. `python-service/data/requests` contains the synthetic request files required by the assessment, including the exact duplicate and zero-byte file.

## Observability

LangGraph is used for the answer workflow. LangSmith is optional; set `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` only when external tracing is desired. The assessment can run offline without LangSmith.

## Submission checklist

- public GitHub repository
- README
- both services
- supplied policy data
- synthetic request files
- automated tests
- representative response JSON
- decision note
- production design note
- final commit SHA

## Commands:
cd python-service
python -m uvicorn app.main:app --reload --port 8000

cd spring-boot-service
.\mvnw.cmd clean test
.\mvnw.cmd spring-boot:run
