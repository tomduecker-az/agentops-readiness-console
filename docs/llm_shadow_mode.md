# LLM Shadow Mode

## Purpose

LLM shadow mode evaluates whether model-based workflow analysis adds practical value without allowing the model to control execution.

The deterministic pipeline remains the governed baseline. The LLM produces a separate advisory artifact that can be inspected, evaluated, and compared against the baseline output.

## Why Shadow Mode Exists

The project should not assume that fluent model output is correct.

Shadow mode allows the system to test:

- whether the LLM understands an unfamiliar workflow packet
- whether the LLM identifies useful risks and controls
- whether the LLM avoids unsupported claims
- whether the LLM avoids domain leakage from prior examples
- whether the LLM produces implementation recommendations that are specific and useful
- whether the LLM output improves on the deterministic baseline

## Scope

LLM shadow mode may:

- read workflow packet content
- produce advisory workflow analysis
- identify missing information
- recommend controls
- recommend HITL gates
- recommend implementation backlog ideas
- persist an advisory artifact
- write audit events showing that the shadow analysis ran

LLM shadow mode may not:

- approve backlog items
- create GitHub issues
- execute write actions
- override policy checks
- bypass human approval
- directly modify workflow state outside the application service layer

## Artifact

LLM shadow mode creates an artifact with type:

```text
llm_workflow_analysis