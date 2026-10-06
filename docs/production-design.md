# Production Design

## 1. High-Level Architecture


                         ┌──────────────────┐
                         │      Client      │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │   Spring Boot    │
                         │   Public API     │
                         │      :8080       │
                         └────────┬─────────┘
                                  │
                           Internal HTTP
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Python Service   │
                         │      :8000       │
                         │                  │
                         │ Document         │
                         │ Extraction       │
                         │                  │
                         │ Policy Retrieval │
                         │                  │
                         │ Answer Workflow  │
                         └────────┬─────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
             ┌──────────────┐           ┌──────────────┐
             │ Policy Store │           │Model Provider│
             └──────────────┘           └──────────────┘


The system uses a two-service architecture.

Spring Boot is the public API layer, while the Python service handles document processing, policy retrieval, and answer generation.

This separation keeps the public API contract independent from the Python policy-processing implementation.

---

## 2. Spring Boot API Layer

Spring Boot owns the public API boundary.

Responsibilities include:

- Exposing `POST /answer`
- Exposing `POST /batches`
- Validating incoming requests
- Receiving caller context
- Forwarding caller identity to the Python service
- Forwarding batch metadata and documents
- Mapping downstream service failures to appropriate HTTP responses

The caller identity is passed through the `X-Caller-Id` header.

The public API should not allow employee-submitted document content to override the caller identity.

---

## 3. Python Processing Layer

The Python service is responsible for:

- Document extraction
- TXT processing
- Text-based PDF processing
- Structured field extraction
- Policy retrieval
- Policy eligibility filtering
- Policy answer generation
- Citation generation
- Batch processing
- Per-document failure isolation

The Python service exposes internal endpoints used by Spring Boot.

```text
POST /internal/answer
POST /internal/batches
```

These endpoints are not intended to be the public API boundary.

---

## 4. Policy Store

The current assessment uses the supplied synthetic policy corpus.

In a production system, the policy corpus should be stored in a persistent policy store rather than relying on application-local files.

A policy record should contain metadata such as:

- Policy ID
- Tenant
- Role
- Status
- Effective start date
- Effective end date
- Benefit/category
- Policy content
- Version
- Source/reference

The policy store should support efficient filtering by:

- Tenant
- Role
- Policy status
- Effective dates
- Benefit

---

## 5. Policy Eligibility

Only eligible policy evidence should be considered for an answer.

Conceptually, policy selection should apply:

```text
tenant matches caller tenant
AND
role matches caller role
AND
status = Approved
AND
effective_start <= as_of
AND
(
    effective_end IS NULL
    OR
    as_of < effective_end
)
```

The effective start date is inclusive.

The effective end date is exclusive.

This prevents historical, future, draft, or cross-tenant policies from being incorrectly used.

---

## 6. Tenant Isolation

Tenant isolation is enforced using the caller context.

For example, an Atlas employee must not receive Boreal employee policy evidence merely because the employee's submitted request mentions Boreal.

The caller context must come from the API request rather than from untrusted document content.

Employee documents are treated as untrusted input.

Instructions contained inside documents must not modify:

- Caller identity
- Tenant
- Role
- Policy eligibility
- Authorization context

---

## 7. Policy Conflict Handling

If multiple simultaneously applicable policies provide contradictory guidance and there is no defined precedence rule, the system should return:

```text
CONFLICT
```

The system should not silently select one policy simply because it was retrieved first.

This makes policy ambiguity visible to downstream consumers and human reviewers.

---

## 8. Evidence and Citations

Policy answers should be grounded in eligible policy evidence.

An `ANSWERED` response should include citations identifying the supporting policy evidence.

The system should avoid relying on:

- General world knowledge
- Unsupported assumptions
- Employee-submitted text as policy evidence
- Irrelevant keyword matches

If sufficient eligible evidence cannot be found, the system should return:

```text
INSUFFICIENT_EVIDENCE
```

rather than inventing a policy answer.

---

## 9. Model Provider

In a production implementation, the model provider should be accessed through an abstraction/interface rather than being tightly coupled to the workflow.

For example:

```text
PolicyAnswerProvider
        │
        ├── ProductionProvider
        │
        └── TestProvider
```

This allows controlled testing of:

- Successful generation
- Provider timeout
- Provider unavailable
- Malformed model output

The provider should have:

- Bounded timeout
- Structured output validation
- Maximum response size
- Explicit error handling

---

## 10. Technical Failure Handling

Technical failures must remain separate from policy outcomes.

Examples of technical failures include:

```text
EMPTY_FILE
UNREADABLE_FILE
ITEM_PROCESSING_FAILURE
PROVIDER_TIMEOUT
PROVIDER_UNAVAILABLE
MALFORMED_MODEL_OUTPUT
```

These must not be incorrectly converted into:

```text
INSUFFICIENT_EVIDENCE
```

`INSUFFICIENT_EVIDENCE` means the system successfully processed the request but could not find sufficient eligible policy evidence.

A technical failure means processing itself did not complete successfully.

---

## 11. Batch Processing

The batch API processes each document independently.

Conceptually:

```text
Batch
 │
 ├── Document 1 → Process
 │
 ├── Document 2 → Process
 │
 ├── Document 3 → Process
 │
 ├── Document 4 → Process
 │
 └── Document N → Process
```

A failure in one document must not stop processing of the remaining documents.

Each document produces an independent result containing information such as:

- Document ID
- Processing status
- Extracted fields
- Field evidence
- Policy result
- Review requirement
- Issues
- Duplicate relationship
- Error information

The manifest order should be preserved in the response.

---

## 12. Duplicate Detection

Exact duplicate files can be detected using a SHA-256 hash of the uploaded file bytes.

For example:

```text
request-01
    │
    └── SHA-256 = ABC123

request-06
    │
    └── SHA-256 = ABC123
```

The second document can then be reported as:

```text
EXACT_DUPLICATE_FILE
```

with:

```text
duplicate_of = request-01
```

This is deterministic and does not depend on model interpretation.

---

## 13. Document Processing

The production document-processing layer should support controlled file handling.

For the assessment, the system supports:

- UTF-8 TXT files
- Text-based PDF files

For production, additional controls should include:

- File-size limits
- Allowed MIME types
- File-extension validation
- Malicious-file scanning
- Temporary-file cleanup
- Parser timeouts
- Protection against resource exhaustion

Scanned PDFs would require an OCR pipeline if they were supported in a future version.

---

## 14. Batch Scalability

The assessment requires synchronous batch processing.

For larger production workloads, the batch workflow can be converted to an asynchronous architecture:

```text
Client
   │
   ▼
Spring Boot
   │
   ▼
Job Queue
   │
   ▼
Batch Worker
   │
   ├── Document Extraction
   │
   ├── Field Extraction
   │
   └── Policy Processing
   │
   ▼
Result Store
```

The public API could return a batch/job ID and provide a separate endpoint for retrieving processing status.

This avoids keeping an HTTP request open for long-running batches.

---

## 15. Timeout and Retry Strategy

For the synchronous assessment workflow:

- Use bounded provider timeouts.
- Allow at most one generation attempt.
- Do not perform automatic retries.

This prevents a slow or unavailable model provider from causing unbounded request latency.

For an asynchronous production architecture, controlled retries could be introduced through a queue, provided that processing is idempotent.

---

## 16. Idempotency

Production batch processing should use idempotency keys or batch IDs to prevent accidental duplicate processing when clients retry requests.

A suitable design could use:

```text
batch_id
+
document_id
+
content hash
```

to identify a processing operation.

This is especially important if batch processing is moved to an asynchronous queue.

---

## 17. Observability

Each request should have a correlation ID.

Logs and traces should be associated with:

- Correlation ID
- Caller ID
- Batch ID
- Document ID
- Policy ID
- Processing duration
- Provider latency
- Failure code

Sensitive employee document contents should not be written directly to logs.

Useful metrics include:

- Request count
- Request latency
- Batch processing duration
- `ANSWERED` count
- `INSUFFICIENT_EVIDENCE` count
- `CONFLICT` count
- Provider failure count
- Document failure count
- Duplicate document count
- Batch completion rate

---

## 18. Security

A production deployment should include:

- HTTPS
- Authentication
- Authorization
- Tenant isolation
- Request-size limits
- File validation
- Malware scanning
- Secret management
- Audit logging
- Access controls

Secrets such as API keys and database credentials must not be committed to Git.

Employee-submitted documents must be considered untrusted input.

Prompt injection inside a document must not be able to change caller authorization or policy selection.

---

## 19. Availability

Spring Boot and Python services should be independently deployable.

A production deployment could use multiple instances:

```text
                 Load Balancer
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
   Spring Boot #1          Spring Boot #2
          │                       │
          └───────────┬───────────┘
                      ▼
              Python Services
               ┌──────┴──────┐
               ▼             ▼
           Python #1     Python #2
```

Health and readiness checks should be used so unhealthy instances are removed from service.

---

## 20. Data Retention

Uploaded employee documents should have an explicit retention policy.

Temporary files created during processing should be deleted after processing.

If documents or results are persisted, storage should provide:

- Encryption at rest
- Access control
- Retention policies
- Auditability

Only the information required for the business workflow should be retained.

---

## 21. Human Review

The system should expose review requirements rather than making unsupported business decisions.

For ambiguous or conflicting employee requests, the result should provide diagnostic information explaining why human review is required.

Examples include:

```text
AMOUNT_MISSING_OR_AMBIGUOUS
POLICY_CONFLICT
BENEFIT_MISSING_OR_UNRESOLVED
HUMAN_REVIEW_REQUIRED
```

This allows the system to automate evidence gathering while keeping unsupported conclusions out of the final workflow.

---

## 22. Future Improvements

Potential production improvements include:

- Asynchronous batch processing
- Persistent batch result storage
- Policy version management
- Explicit policy precedence rules
- OCR support for scanned documents
- More advanced document extraction
- Human-review interface
- Distributed tracing
- Centralized logging
- Provider fallback strategies
- Policy indexing/search infrastructure
- Stronger schema validation
- Automated policy-source refresh workflows

The key production principle is to preserve the separation between **caller authorization, policy eligibility, document processing, model generation, and human review** so that failures or untrusted input in one layer cannot silently change decisions in another.