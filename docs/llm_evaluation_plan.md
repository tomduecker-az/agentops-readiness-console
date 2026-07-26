# LLM Evaluation Plan

## Purpose

The AgentOps Readiness Console should not be judged only by whether it can generate structured JSON.

The core question is whether the system can analyze an unfamiliar workflow packet and produce useful, grounded, defensible workflow-readiness artifacts.

This plan defines how workflow analysis quality will be evaluated before and after LLM-backed reasoning is introduced.

## Evaluation Principle

The system must prove that its outputs are:

- grounded in the uploaded workflow packet
- specific to the workflow being analyzed
- free from domain leakage from prior examples
- useful to a business, technology, or governance reviewer
- structured enough to drive implementation work
- safe enough to support approval-gated automation

## Current Baseline

The current system uses deterministic specialist modules.

This is intentional for the MVP because it validates:

- workflow packet ingestion
- artifact contracts
- policy checks
- data sensitivity classification
- approval-gated write actions
- audit event persistence
- Supabase-backed run history
- workflow-neutral risk and backlog patterns

LLM-backed reasoning should improve analysis quality without bypassing these controls.

## Future LLM-Backed Mode

A future LLM-backed mode should:

- read only approved workflow packet content
- produce schema-constrained outputs
- cite or reference workflow evidence where possible
- avoid inventing systems, policies, actors, or facts
- allow deterministic policy and approval logic to remain outside the model
- persist prompt metadata, model metadata, output artifacts, and evaluation results

## Evaluation Categories

### 1. Workflow Understanding

The system should correctly identify:

- workflow steps
- actors
- handoffs
- systems or records
- decision points
- approval points
- candidate automation points

### 2. Data Sensitivity

The system should identify:

- PII
- confidential operational data
- sensitive free-text fields
- fields that should be blocked from model context
- fields requiring redaction

### 3. Risk Identification

The system should identify workflow-relevant risks such as:

- required approval bypass
- missing source or intake information
- uncontrolled write actions
- external commitment risk
- scope or requirement change risk
- technical integration or system access risk
- handoff quality risk
- timeline or SLA pressure
- sensitive data entering model context

### 4. Control Mapping

The system should map risks to practical controls, including:

- human approval gates
- validation checks
- audit logging
- review queues
- escalation rules
- model-context restrictions
- write-action guardrails

### 5. HITL Design

The system should recommend:

- where human review is required
- what the agent can do before approval
- what is blocked without approval
- who should review
- what evidence is required
- when escalation should happen

### 6. Implementation Backlog

The backlog should contain:

- clear implementation items
- source risk IDs
- source control IDs
- recommended owners
- approval requirements
- practical descriptions
- workflow-neutral language

### 7. Grounding and Non-Hallucination

The output should not introduce:

- systems not mentioned in the workflow packet
- policies not implied by the packet or policy catalog
- actors not described in the process
- domain language from another workflow
- unsupported automation recommendations

### 8. Enterprise Usefulness

A reviewer should be able to answer:

- What are the major risks?
- What should not be automated yet?
- Where is human approval required?
- What data cannot safely enter model context?
- What should engineering build first?
- What evidence exists for the recommendation?

## Acceptance Threshold

For portfolio readiness, an unfamiliar workflow should score at least 80 out of 100 on the evaluation harness.

Scores below 80 indicate that the analysis may be structured but not yet useful enough to support the project’s core claim.

## Next Milestones

1. Add an unseen workflow packet.
2. Evaluate deterministic baseline output.
3. Add LLM-backed workflow analysis mode.
4. Compare deterministic and LLM-backed outputs.
5. Persist evaluation results.
6. Add human review notes for selected examples.