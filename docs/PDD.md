# Runback — Product Design Document

**Status:** Product vision  
**Version:** 1.0  
**Date:** 21 November 2026

## 1. Design goal

Make a complex agent run understandable at a glance, then make the next debugging action obvious. The interface should move from broad signals to trace evidence to a repeatable fix workflow:

**Project health → run list → trace timeline → evidence-backed diagnosis → replay/compare → evaluation case → CI result**

Runback is a technical tool. The design should feel precise and calm, with dense information available on demand and clear hierarchy for errors, durations, and relationships.

## 2. Product experience model

### Information architecture

1. **Workspace** — members, roles, retention, redaction, provider configuration, audit log.
2. **Projects** — connected applications, environments, SDK keys, integrations, and project-level policies.
3. **Runs** — searchable list of agent executions and saved views.
4. **Run detail** — trace tree, timeline, span inspector, diagnosis, replay, comparison, and case creation.
5. **Evaluations** — cases, suites, baselines, runs, score history, and CI settings.
6. **Integrations** — Python SDK, framework adapters, OTLP endpoint, API tokens, CI provider, and local model providers.

### Global navigation

- Workspace/project switcher.
- Primary navigation: Overview, Runs, Evaluations, Integrations, Settings.
- Search across trace IDs, agent names, tools, errors, tags, and case names.
- Environment and time-range filters remain visible in run-oriented views.
- Persistent privacy indicator when payload capture or AI analysis is disabled by policy.

## 3. Core screens

### 3.1 Project overview

Purpose: answer “are agent runs healthy, and where should I look?”

Components:

- Run volume and success/error trend.
- Evaluation pass rate and recent regressions.
- Latency distribution with p50/p95, where enough data exists.
- Top failure categories, tools, and agent versions.
- Recent failed runs and recently changed evaluation results.
- Integration health and last-ingested timestamp.

Every chart supports a click-through to the filtered run list. Avoid false precision when sample sizes are small.

### 3.2 Runs explorer

Purpose: find the relevant execution quickly.

Table columns: status, run name/agent, start time, duration, environment, version/commit, framework, and tags. Filters include status, date, agent, framework, environment, error, model, and tool. Support saved views and cursor-based pagination.

Empty state explains how to connect an SDK or import a trace. Error states distinguish invalid payload, authentication failure, ingestion delay, and network issue.

### 3.3 Run detail

Purpose: explain one execution using navigable evidence.

Layout:

- Header: run status, trace ID, environment, agent version, duration, time, and actions.
- Left pane: collapsible parent-child trace tree, grouped by agent turn or workflow phase when source data permits.
- Center pane: chronological waterfall with duration, status, type, and error markers.
- Right pane: selected span inspector with input/output, tool arguments/results, metadata, errors, and redaction state.
- Secondary tabs: Summary, Diagnosis, Replay, Compare, Comments.

Selecting an item synchronizes all three panes. Deep links preserve selected span and open tab. Large payloads are collapsed by default with copy/download actions controlled by permissions.

### 3.4 Diagnosis view

Purpose: help a developer test a likely explanation.

Each diagnosis card contains:

- Short summary and severity.
- Category, such as tool failure, bad routing, retrieval mismatch, schema violation, latency, or policy rejection.
- Evidence references that link to exact spans and payload fields.
- Confidence label with a short explanation of uncertainty.
- Suggested reproduction steps and candidate assertions.
- Actions: “create evaluation case,” “add comment,” or “dismiss.”

Separate **Observed** details from **Hypothesis**. If the analyst cannot cite trace evidence, it must say that the trace is insufficient. The UI should never imply an AI hypothesis is a verified root cause.

### 3.5 Replay and branch view

Purpose: understand and safely test alternate behavior.

Display a mode banner at all times:

- **Recorded playback:** renders stored events; no agent or tools execute.
- **Mocked replay:** reruns selected logic while replacing model/tool responses with recorded fixtures.
- **Sandbox replay:** executes allowed tools in an isolated environment.
- **Live replay:** calls configured model/tool providers and may have costs or external effects.

Require explicit confirmation before sandbox or live mode. Show the selected start step, changed inputs, dependency fixtures, provider, and side-effect policy before execution. Preserve the source trace and create a linked child run for each branch.

### 3.6 Compare runs

Purpose: identify behavior changes between baseline and candidate.

- Choose baseline and candidate runs, or compare a run to a saved case.
- Align matching steps by stable source identifiers when available, then fall back to span type/name/parent path.
- Highlight added, removed, reordered, failed, changed-output, and latency-regressed steps.
- Support JSON structural diff and selectable text diff.
- Show uncomparable fields and reasons; do not silently treat missing data as equal.
- Convert selected differences into assertions or a case.

### 3.7 Evaluation suite

Purpose: turn known behavior into a release check.

- Suite list with owner, branch/commit, latest pass rate, trend, and gate status.
- Case editor with initial input, fixtures, expected assertions, tags, and source trace.
- Run history with per-case results and evidence links.
- Threshold and required-case configuration, with a review step before a CI gate changes.
- Exportable JSON result for CI.

### 3.8 Integrations and setup

Guided connection flow:

1. Create project and environment.
2. Choose SDK/framework or OTLP route.
3. Select capture policy and redaction defaults.
4. Copy a generated setup snippet and create a scoped ingest token.
5. Send a test run and view the received trace.
6. Optionally connect CI and a diagnosis model provider.

Secrets are shown only at creation time. The UI explains what data the integration collects before activation.

## 4. Key user journeys

### Journey A: debug a bad production run

Open alert or run link → inspect trace timeline → select failing tool/model span → review input, output, and error → open evidence-backed diagnosis → branch with recorded or mocked responses → save the failing behavior as an evaluation case → assign/comment and share the trace.

### Journey B: check a prompt or agent change

Open evaluation suite → select baseline and candidate version → run cases → inspect changed outputs and steps → approve expected changes or fix regressions → use CI status to gate the release.

### Journey C: connect a new framework

Create project → select framework adapter or OTLP → set privacy policy → configure SDK → send test trace → validate parentage and payload visibility → enable capture for the environment.

## 5. Interaction and content rules

- Use stable terminology: **trace** for an end-to-end run, **span** for a timed operation, **event** for an occurrence, **case** for a reusable evaluation input, **suite** for a group of cases.
- Reserve **replay** for a clearly labeled mode; never use it without saying whether it is recorded, mocked, sandboxed, or live.
- Status is communicated with text and iconography as well as color.
- Destructive actions (delete, revoke token, remove case) require contextual confirmation and explain the scope.
- Redacted values show that data was withheld and, when allowed, why; never imply an empty value was the original content.
- Long content uses structured JSON/tree views, syntax highlighting, copy controls, and bounded rendering.
- Errors provide a recovery action and a correlation ID where applicable.

## 6. Visual and accessibility direction

- Dense desktop-first console with responsive layouts for review and triage.
- Neutral dark/light themes, with a strong semantic palette reserved for status and severity.
- Timeline alignment uses spacing and labels, not color alone.
- Keyboard support for tree navigation, tabs, filters, command search, and diff navigation.
- Minimum readable contrast and visible focus indicators; avoid animation as the sole cue for state changes.
- Respect reduced-motion preferences and allow payload font scaling.

## 7. Design states to cover

- New workspace with no project.
- Project configured but no trace received.
- Trace with success, failure, partial payload redaction, malformed spans, missing parent, and very large span count.
- Ingestion in progress, delayed, rejected, and retried.
- Diagnosis disabled by policy, unavailable, still processing, low confidence, and complete.
- Replay blocked by policy, missing fixtures, successful, failed, and canceled.
- Evaluation suite with no cases, mixed results, regression, and no comparable baseline.
- User without permission to view payload, export data, or change project policy.

## 8. Product metrics in the interface

Show denominators and time windows alongside pass rates and failure percentages. Make clear whether metrics come from all ingested runs, sampled runs, or evaluation suites. Provide drill-down for every aggregate. Avoid presenting AI confidence as a calibrated probability unless calibration has been measured.

