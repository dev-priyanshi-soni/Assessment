# Production design note

For 10,000 daily requests containing personal information, I would deploy the Spring Boot gateway and Python service as separate containerized services behind an API gateway/load balancer. Authentication and authorization would use a trusted identity provider rather than a caller header. Secrets would be stored in a managed secret store, TLS enforced end-to-end, and structured logs would contain request, batch, and document identifiers but not document contents or credentials.

I would add rate limiting, audit trails, encryption at rest, dependency and container scanning, provider timeouts, circuit breakers, metrics, distributed tracing, alerting, and durable policy versioning. Retrieval would remain metadata-filtered before generation. A slow approval system would be isolated behind an idempotent integration with explicit human-review states.

The main risks are cross-tenant data leakage, prompt injection, sensitive information in logs, incorrect policy retrieval, provider failure, and duplicate/partial processing. Before committing to delivery dates I would clarify the identity source, policy ownership and precedence rules, approval-system API/SLA, retention/deletion requirements, file-size/type limits, compliance requirements, and latency/availability targets.
