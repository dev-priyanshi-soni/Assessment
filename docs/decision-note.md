# Decision note

## Consequential design choice
The policy corpus is treated as structured policy data first. Caller tenant/role, approval state, and effective dates are hard filters before semantic retrieval. FAISS is used locally for semantic candidate retrieval.

## Alternative rejected
A hosted vector database and mandatory hosted LLM were rejected because the assessment requires a deterministic offline model double and supplies only a small policy corpus.

## Main limitation
The local deterministic embedding is suitable for an offline assessment but is not a production semantic embedding model. A production version should use a versioned embedding model and a durable vector index.

## AI assistance
AI coding assistance was used during implementation. The candidate remains responsible for reviewing, testing, and explaining the implementation.
