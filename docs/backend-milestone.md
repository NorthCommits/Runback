# Runback Backend Milestones

**Status:** Proposed delivery plan
**Source documents:** `docs/PDD.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`
**Implementation order:** Backend completely before frontend work begins

## Delivery contract

- All backend application code, tests, migrations, containers, and backend configuration live under `backend/`.
- The backend is Python and is runnable only through Docker for supported local development and CI workflows.
- The API is versioned under `/api/v1`; the frontend consumes the API and never accesses storage directly.
- The canonical trace model, not any agent framework, is the product boundary. Framework support is implemented as adapters.
- Every persisted payload is redacted according to project policy before storage or external-model use.
- Recorded replay and deterministic evaluation must work with no model-provider credentials.
- Frontend implementation begins only after the Backend Completion Gate passes. API contracts and OpenAPI output may be prepared during backend work, but no frontend application code is part of these milestones.

## Proposed backend layout

```text
backend/
  app/
    api/v1/                 # HTTP route handlers and dependency wiring
    core/                   # settings, security, logging, errors
    domain/                 # canonical models, validation, policies
    services/               # ingestion, comparison, replay, evaluation, diagnosis
    repositories/           # persistence contracts and implementations
    workers/                # queued job handlers and scheduling
    adapters/               # OTLP and framework-to-canonical translators
    infrastructure/         # database, queue, object-store integrations
    main.py
  migrations/
  tests/
    unit/
    integration/
    contract/
    fixtures/
  scripts/
  Dockerfile
  docker-compose.yml
  pyproject.toml
  alembic.ini
  .env.example
```

Route handlers only validate transport concerns and call services. Services enforce business and safety rules. Repositories own data access. Adapters translate external records but do not leak framework types into the domain model.

## Engineering rules

- Use explicit types, focused functions, meaningful names, small modules, and tests as the primary explanation of behavior.
- Do not add docstrings or comments unless a safety, interoperability, or non-obvious invariant cannot be expressed clearly in code.
- Validate at boundaries with Pydantic models; keep internal domain types independent from transport and ORM models.
- Use database migrations for all persistent-schema changes. Never create schema implicitly at application startup.
- Keep each feature as a tested vertical slice and commit it independently after verification.
- Treat trace content as untrusted data: do not interpolate it into system instructions, logs, or error responses.

## Milestones

### M0 — Repository and container foundation

**Goal:** Establish a reproducible Python service that is safe to extend.

**Complete when:**

- [ ] `backend/` contains the proposed package structure, dependency manifest, test configuration, formatter/linter/type-checker configuration, and environment template.
- [ ] `backend/Dockerfile` builds a non-root production image with no development secrets baked in.
- [ ] `backend/docker-compose.yml` starts the API, PostgreSQL, a worker process, and required local dependencies with named persistent volumes.
- [ ] A health endpoint reports application and dependency readiness without exposing credentials or configuration values.
- [ ] CI can build the image and run unit tests, integration tests, linting, and type checking from a clean checkout.
- [ ] Local and CI commands are documented in the root README or a backend runbook.

**Verification:** `docker compose -f backend/docker-compose.yml up --build`, health check, migrations, and the complete quality suite pass.

### M1 — Tenant-aware core and canonical persistence

**Goal:** Create the data foundation that preserves trace identity, parentage, and policy context.

**Complete when:**

- [ ] Migrations define workspaces/tenants, projects, environments, scoped ingest tokens, traces, spans, payload references, and audit records.
- [ ] The canonical trace and span models preserve the fields defined in the architecture, including source/schema versions, timestamps, status, attributes, events, links, and replay lineage.
- [ ] Tenant and project identity are enforced in repository queries and worker job payloads.
- [ ] Project-scoped token creation, revocation, hashing, and authorization are implemented without ever returning a stored token value.
- [ ] Unique constraints support idempotent ingestion and prevent duplicate spans within a trace.
- [ ] Migration upgrade and downgrade paths are exercised against a fresh PostgreSQL container.

**Verification:** migration tests, tenant-isolation integration tests, token authorization tests, and duplicate-constraint tests pass.

### M2 — Secure Runback trace ingestion

**Goal:** Deliver the first usable vertical slice: send a canonical trace, redact it, persist it idempotently, and retrieve it safely.

**Complete when:**

- [ ] `POST /api/v1/ingest/traces` accepts a versioned JSON batch, applies request/size limits, and returns structured validation failures with a correlation ID.
- [ ] Parent-child span relationships, source IDs, ordering, status, timestamps, and metadata survive normalization.
- [ ] Capture and redaction policies run before payload persistence; tests prove secrets and masked fields cannot be retrieved from storage or logs.
- [ ] Idempotency keys make a repeated successful request safe and observable without creating duplicate traces or spans.
- [ ] Large payloads use a bounded payload-reference abstraction, with a local filesystem implementation suitable for Docker development.
- [ ] A fixture-based sample trace can be ingested entirely through the public API.

**Verification:** API contract tests cover valid, malformed, oversized, unauthorized, redacted, and duplicate ingestion batches.

### M3 — Trace query, inspection, and deterministic comparison

**Goal:** Supply all read-side contracts required for the runs explorer and run-detail experience.

**Complete when:**

- [ ] Cursor-paginated trace search supports project, environment, status, date, agent, framework, model, tool, error, version, and tag filters.
- [ ] `GET /api/v1/traces/{trace_id}` returns an authorized normalized trace, ordered spans, payload visibility/redaction state, and computed duration summary.
- [ ] Deep-link query parameters can select a span without relaxing authorization.
- [ ] The comparison service aligns stable source identifiers first, then documented fallback identity; it returns added, removed, reordered, failed, changed-output, latency-regressed, and uncomparable fields.
- [ ] Payload and result limits prevent a large trace or diff from exhausting API resources.
- [ ] Database indexes are measured against representative fixtures and added only for demonstrated query paths.

**Verification:** pagination, filter, authorization, parentage, comparison, and large-run integration tests pass.

### M4 — Cases, recorded replay, and deterministic evaluation

**Goal:** Convert known behavior into regression checks without re-executing user tools.

**Complete when:**

- [ ] A trace or selected span creates a versioned evaluation case with immutable source reference, fixtures, assertions, tags, review state, and audit event.
- [ ] Recorded replay returns stored steps and clearly identifies itself as non-executing playback.
- [ ] Evaluation suites run deterministic assertions for schema, tool sequence, required evidence, refusal behavior, and output constraints.
- [ ] Evaluation results record candidate version, suite/case version, assertion results, baseline delta, and artifact references.
- [ ] The suite API exposes status and machine-readable results suitable for a future CLI/CI caller.
- [ ] No replay or evaluation path can make a provider or tool call in recorded mode.

**Verification:** fixture-only end-to-end tests prove repeated evaluation is deterministic and tool/provider call mocks remain unused.

### M5 — OTLP, SDK, and framework adapters

**Goal:** Add integrations without coupling Runback’s core to a vendor runtime.

**Complete when:**

- [ ] `POST /api/v1/otlp/v1/traces` translates supported OTLP input into the canonical model while preserving source identifiers and parentage.
- [ ] A Python SDK exposes run/span capture, transport, capture configuration, redaction hooks, batching, retry behavior, and schema-version metadata.
- [ ] A documented adapter protocol maps LangGraph, OpenAI Agents SDK, and CrewAI observations into canonical events; adapter and source-framework versions are stored on each trace.
- [ ] LangGraph integration is optional and uses persisted checkpoint state with a unique `thread_id` per independent diagnosis run.
- [ ] The OpenAI Agents adapter owns redaction and delivery in one replacement trace processor when export depends on successful redaction; it does not leave an unsafe default exporter active.
- [ ] The CrewAI adapter observes the event bus or hooks and isolates adapter failures so application execution is not changed.
- [ ] Every adapter is proven with recorded fixtures and a compatibility matrix of supported framework versions.

**Verification:** SDK transport tests, OTLP contract fixtures, and adapter fixtures pass with no live model credentials.

### M6 — Worker platform and evidence-backed diagnosis

**Goal:** Run deferred work reliably and add optional diagnosis without making the core dependent on an LLM.

**Complete when:**

- [ ] Durable worker jobs exist for analysis, evaluation, export, retention, and notifications; jobs carry tenant/project identity, are idempotent, expose retry state, and enforce access policy at execution time.
- [ ] Deterministic evidence gathering and anomaly checks can produce a diagnosis result with cited span IDs without invoking a model.
- [ ] The optional LangGraph workflow follows classify → gather evidence → deterministic checks → hypothesis → suggested tests → policy/confidence → persisted reviewable result.
- [ ] Human review pauses and resumes use a persistent checkpointer and a stable run-specific `thread_id`; resumption cannot duplicate external effects.
- [ ] Provider access is behind an interface; model payloads are redacted according to policy before any provider request.
- [ ] Hypotheses always separate observed evidence from inference, include confidence labels, and never execute user tools.

**Verification:** worker retry, no-model diagnosis, cited-evidence, policy-denial, and pause/resume tests pass.

### M7 — Controlled branch replay and CI interface

**Goal:** Safely expand beyond playback while making execution modes impossible to confuse.

**Complete when:**

- [ ] Mocked replay runs only against recorded model/tool fixtures and creates a linked child trace with fixture provenance.
- [ ] Sandbox replay executes only in isolated workers with an allowlisted tool policy, explicit time/resource limits, and cancellation.
- [ ] Live replay requires explicit confirmation, enabled project policy, configured provider credentials, and auditable side-effect approval.
- [ ] Each replay response and child trace records mode, source trace, start step, edited inputs, and determinism label.
- [ ] A CLI-friendly endpoint or command starts immutable suite versions, returns machine-readable results and artifacts, and uses scoped CI credentials.
- [ ] Regression gate policy can pass, warn, or block without permitting external calls unless its policy explicitly allows them.

**Verification:** security tests reject unauthorized modes; mocked/sandboxed/live policy tests prove the correct guardrails and audit events.

### M8 — Team controls, governance, and lifecycle operations

**Goal:** Make the backend safe for shared and production use.

**Complete when:**

- [ ] User authentication and workspace roles protect all user-facing API actions; project ingest tokens remain separate from user identity.
- [ ] Comments, annotations, assignments, tags, internal sharing permissions, and audit history are tenant-scoped.
- [ ] Retention, export, and deletion policies remove primary records, payload objects, derived analyses, and exports consistently.
- [ ] Quotas cover request rate, trace volume, payload size, background work, and external-provider usage.
- [ ] Structured logs, metrics, and traces provide operational visibility while excluding payloads and preventing recursive self-capture.
- [ ] Export and policy-change events are auditable; secrets are stored only through the configured secret-management boundary.

**Verification:** role matrix, deletion/retention, quota, audit, and observability tests pass against Docker services.

### M9 — Backend release readiness

**Goal:** Prove that the backend is complete, operable, and ready to become the contract for frontend work.

**Complete when:**

- [ ] All P0 requirements (FR-01 through FR-07) are complete and every P1 requirement has either been implemented or has an explicitly accepted, versioned deferral.
- [ ] The OpenAPI contract is generated, versioned, and covered by API contract tests.
- [ ] A clean Docker environment can initialize, migrate, ingest sample traces, search a run, compare traces, create a case, run a deterministic suite, and retrieve results end to end.
- [ ] Security review covers tenant isolation, authentication, token handling, redaction, replay authorization, request limits, and untrusted-trace handling.
- [ ] Failure handling covers database/queue/object-store outages, job retries, cancellation, schema compatibility, backup/restore, and correlation IDs.
- [ ] Performance baselines exist for ingestion, query pagination, large traces, and background throughput, with documented limits.
- [ ] Deployment manifests, environment configuration, release checklist, and operator runbook are complete for local, hosted, and self-hosted profiles.

**Verification:** full Docker end-to-end suite, load smoke tests, migration rehearsal, security test pass, and release checklist sign-off.

## Backend Completion Gate

Frontend work may begin only when M0–M9 are complete and the following are demonstrably true:

- [ ] The API contract is stable enough to version and publish.
- [ ] Docker is the supported reproducible way to run the backend and its dependencies.
- [ ] Core trace capture, redaction, retrieval, comparison, cases, recorded replay, and deterministic evaluation work end to end.
- [ ] Agentic integrations and diagnosis remain optional, evidence-linked, policy-governed, and safe with no model key.
- [ ] The backend has test, security, operational, and migration evidence suitable for frontend teams to depend on.

## Frontend handoff after the gate

The frontend starts only after the gate above. It consumes the generated versioned API contract and is delivered in this order: project/run explorer → trace detail and span inspector → comparison and cases → evaluation results → replay/diagnosis → workspace governance. Any API change after handoff requires a backward-compatible version or coordinated contract migration.

## Risks to resolve early

| Risk | Mitigation and milestone |
|---|---|
| Captured payloads expose secrets or personal data | Redaction before persistence, payload isolation, and retrieval authorization in M2; enforce again before model calls in M6. |
| A framework adapter changes application behavior | Treat adapters as isolated observers with fixture compatibility tests in M5. |
| Replay accidentally repeats side effects | Recorded playback first; explicit separate mode policies and deny-by-default execution in M4 and M7. |
| Diagnosis overstates a cause | Persist citations, label hypotheses, and maintain deterministic no-model checks in M6. |
| Queue/database retries duplicate data or jobs | Idempotency keys, unique constraints, and idempotent jobs from M1 onward. |
| The frontend becomes coupled to storage details | Freeze a versioned API contract at M9 and prohibit direct storage access. |
