# Runback — Product Requirements Document

**Status:** Product vision  
**Version:** 1.0  
**Date:** 21 November 2026  
**Product:** Runback — observability, diagnosis, replay, and evaluation for AI agent systems

## 1. Product summary

Runback helps teams understand why an AI agent run succeeded, failed, or produced a surprising result—and prevent the same failure from returning. It captures an agent run as a structured trace, makes the trace inspectable, lets developers replay or branch it under controlled conditions, and turns useful traces into evaluation cases that can run in development and CI.

Runback is a framework-agnostic product. It accepts traces through SDK integrations and OpenTelemetry-compatible ingestion, then presents them in one consistent data model. It combines deterministic tools—trace search, timeline inspection, diffs, assertions, and replay—with an optional AI diagnosis assistant whose conclusions link back to the evidence in the trace.

## 2. Problem and opportunity

Agent workflows cross model calls, tools, handoffs, retrieval, guardrails, and external services. A bad final answer may be several steps removed from its cause. Logs often omit parent-child relationships or the exact inputs and outputs needed to reproduce the run. Fixes then rely on guesswork, and teams can regress behavior without noticing.

Tracing conventions already describe useful primitives such as trace IDs, parent span IDs, timestamps, attributes, and status. Frameworks also expose different tracing capabilities: OpenAI Agents SDK records model generations, tools, handoffs, and guardrails; LangGraph supports checkpointed graph state and recovery. Runback’s product opportunity is to connect these execution records to an actionable debugging and regression workflow, while keeping ingestion independent of any one framework. See [research notes and references](#12-research-basis).

## 3. Product vision

Make every important agent run explainable, reproducible, and testable. A developer should be able to go from “this agent did something wrong” to “here is the failing step, the likely cause, a repeatable case, and the regression check” without reconstructing the run by hand.

## 4. Target users

### Primary: AI application engineers

Build agentic applications in Python or TypeScript and need to debug tool use, routing, prompts, retrieval, guardrails, and model outputs.

### Secondary: platform and quality engineers

Own shared agent infrastructure, reliability, evaluations, CI gates, data handling, and production incident response across multiple teams.

### Tertiary: technical leads and product owners

Need to review trends in failures, latency, cost, quality, and release risk without reading every raw trace.

## 5. Jobs to be done

- When an agent produces an unexpected result, show me the full causal sequence and identify the step where behavior diverged.
- When I change an agent, let me compare the new run to a known-good or known-bad run.
- When I discover a failure, let me preserve it as a reusable evaluation case.
- When a failure recurs, help me reproduce it without accidentally rerunning side-effecting tools.
- When I use multiple frameworks, let me inspect runs in one consistent interface.
- When I use production data, help me control what is collected, retained, redacted, and accessible.
- When I review an AI-generated diagnosis, show me the trace evidence behind each claim.

## 6. Product principles

1. **Evidence before explanation:** every diagnosis should reference trace steps and distinguish observed facts from hypotheses.
2. **Safe by default:** replay must not repeat external side effects unless the user explicitly enables a controlled live execution.
3. **Framework-neutral core:** adapters translate framework records into a stable Runback model; the product does not require a particular agent runtime.
4. **Useful without paid inference:** search, filtering, trace diffs, assertions, saved cases, and deterministic replay work without an LLM key. AI assistance is optional and provider-configurable.
5. **Local-first development, cloud-ready operations:** developers can inspect local runs; teams can centralize access with workspace controls.
6. **Explicit data handling:** users can see, redact, retain, export, and delete captured content.

## 7. Product capabilities

### 7.1 Run capture and ingestion

- Python SDK and framework integrations that capture run, span, model, tool, retrieval, handoff, guardrail, and error data.
- OpenTelemetry Protocol (OTLP) ingestion plus a Runback JSON import/export format.
- Adapters for LangGraph, OpenAI Agents SDK, and CrewAI, with a documented custom-adapter interface.
- Batch and streaming ingestion, idempotency keys, source/environment/version metadata, and schema versioning.
- Configurable capture policies for inputs, outputs, metadata, and sensitive fields.

### 7.2 Trace exploration

- Hierarchical timeline with parent-child spans, duration, status, type, and run metadata.
- Search and filtering by project, environment, agent, framework, status, date, tags, model, tool, and error.
- Per-step view for inputs, outputs, tool arguments/results, errors, attributes, and raw event data.
- Latency waterfall and aggregate run statistics.
- Deep links to a trace, span, and saved case.

### 7.3 Replay and branching

- Recorded replay that reconstructs the observed sequence from captured data.
- Controlled replay modes: recorded outputs, mocked tools, sandboxed tools, and explicitly enabled live calls.
- Branch from a selected step with edited inputs or configuration; preserve parent-run lineage.
- Replay policies that require confirmation for external side effects and allowlist executable tools.
- Determinism labels that distinguish exact recorded playback from a fresh model/tool execution.

### 7.4 Run comparison and evaluation

- Compare two or more runs by matching step identity, event type, status, duration, structured output, and selected semantic fields.
- Evaluation suites composed of saved traces, manually authored cases, assertions, and scoring rules.
- Deterministic checks for schema validity, tool sequence, required evidence, refusal behavior, and output constraints.
- Optional model-graded checks with evaluator version, prompt, provider, and score provenance recorded.
- Run suites locally, on demand, by schedule, or in CI; show baseline and regression deltas.
- Version evaluation cases and support review/approval before changing a release gate.

### 7.5 AI diagnosis assistant

- Summarize a run and identify candidate failure points from the trace.
- Generate ranked hypotheses with citations to the exact trace steps used as evidence.
- Suggest a reproduction plan, assertions, or a new evaluation case.
- Ask questions against one trace or a selected set of runs.
- Never execute a suggested action or modify a project without explicit user action.
- Support local inference and bring-your-own-provider configuration. Do not require a paid model API for the core product.

### 7.6 Collaboration and incident workflow

- Projects, environments, teams, and role-based access control.
- Comments and annotations on traces, spans, comparisons, and evaluation cases.
- Assignments, status, tags, and incident links for failure triage.
- Shareable internal links with permission checks and audit history.
- Notifications for evaluation regressions and configured production thresholds.

### 7.7 Governance and operations

- Workspace-level retention, deletion, export, and data-region settings.
- Redaction rules applied before storage and before AI-provider requests.
- Secret and personal-data pattern detection with user-configurable masks.
- Audit log for access, exports, policy changes, and deletion.
- Usage controls for trace volume and payload size.
- Self-hosted deployment option and managed cloud option as the product matures.

## 8. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Ingest a valid Runback or OTLP trace and preserve trace/span parentage. | P0 |
| FR-02 | Normalize supported framework events to the Runback canonical model. | P0 |
| FR-03 | Browse, search, and filter traces and inspect individual spans. | P0 |
| FR-04 | Redact configured fields before persistent storage. | P0 |
| FR-05 | Compare runs and identify changed, missing, failed, and slower steps. | P0 |
| FR-06 | Save a trace or selected span as a versioned evaluation case. | P0 |
| FR-07 | Run deterministic recorded replay without repeating external side effects. | P0 |
| FR-08 | Create evaluation suites with deterministic assertions and review results. | P1 |
| FR-09 | Capture supported LangGraph, OpenAI Agents SDK, and CrewAI runs through adapters. | P1 |
| FR-10 | Produce AI-assisted hypotheses with evidence references and confidence. | P1 |
| FR-11 | Run suites from CI and return machine-readable status and artifacts. | P1 |
| FR-12 | Support teams, roles, comments, audit events, retention, and export. | P1 |
| FR-13 | Support safe branch replay with mock, sandbox, and opt-in live modes. | P1 |
| FR-14 | Expose a documented API and adapter SDK for custom frameworks. | P1 |
| FR-15 | Add cost and token tracking when source instrumentation provides reliable usage data. | P2 |

## 9. Non-functional requirements

- **Correctness:** preserve IDs, parentage, timestamps, status, and source metadata; reject malformed traces with actionable validation errors.
- **Security:** tenant isolation, least privilege, secret-safe logging, configurable redaction, encrypted transport and storage in hosted deployments.
- **Privacy:** payload collection is configurable; sensitive payloads are not sent to an AI provider unless the workspace policy allows it.
- **Reliability:** ingestion is idempotent; transient storage or queue failures can be retried without duplicate spans.
- **Performance:** interactive trace views should paginate or virtualize large runs; ingestion should not block on AI analysis.
- **Portability:** JSON/OTLP export and documented schema versioning reduce lock-in.
- **Accessibility:** keyboard-operable navigation, semantic controls, visible focus, and status cues that do not rely on color alone.
- **Observability:** Runback itself emits structured logs, metrics, and traces while preventing recursive capture of its own telemetry.

## 10. Success measures

- Time from selecting a failed run to identifying the failure step.
- Percentage of captured failures converted into reusable evaluation cases.
- Percentage of evaluation regressions caught before deployment.
- Time to integrate a new framework adapter.
- Trace ingestion success rate and duplicate-ingestion rate.
- User-reported usefulness of diagnoses, measured separately from automated model scores.
- Number of replay attempts that accidentally execute a disallowed side effect: target zero.

## 11. Product boundaries and risks

- Runback explains recorded evidence; it cannot guarantee that a model’s causal explanation is correct.
- Recorded replay is not equivalent to rerunning a model. Live replay may vary by model version, sampling, external state, and tool responses.
- Framework trace formats change; adapters and schema compatibility need explicit versioning.
- Captured prompts, tool arguments, and outputs may contain secrets or personal data. Redaction and access control are core product features, not optional polish.
- “Replay” must clearly communicate whether a run is playback, mocked execution, sandboxed execution, or live execution.

## 12. Research basis

Research reviewed 21 November 2026. The sources below inform the product’s tracing model and framework choices; they do not establish that Runback’s product-market fit is validated.

- [OpenTelemetry: traces and spans](https://opentelemetry.io/docs/concepts/signals/traces/) — traces, parent-child spans, context, status, attributes, and export paths.
- [OpenTelemetry: trace semantic conventions](https://opentelemetry.io/docs/specs/semconv/general/trace/) — standardized attributes make cross-language and cross-system traces easier to correlate.
- [OpenAI Agents SDK: tracing](https://openai.github.io/openai-agents-python/tracing/) — built-in tracing includes model generations, tools, handoffs, guardrails, and custom events; the documentation also highlights sensitive payload handling and custom processors.
- [LangGraph: persistence](https://docs.langchain.com/oss/python/langgraph/persistence) — checkpointing supports graph state recovery, time travel, and fault tolerance; this is distinct from a vendor-neutral observability record.
- [CrewAI documentation](https://docs.crewai.com/) — distinguishes agent/crew execution from Flow orchestration and exposes a Python-oriented framework option.

