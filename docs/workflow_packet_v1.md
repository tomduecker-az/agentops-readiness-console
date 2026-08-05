# Workflow Packet v1

## Purpose

Workflow Packet v1 defines the required upload format for an AI Agent Readiness Assessment.

The goal is to let business users provide structured workflow information without writing JSON. The application validates these files, normalizes them into an internal workflow packet, and uses the normalized packet for analysis, diagnostics, blueprints, and reports.

## Design Principles

- Users provide Markdown and CSV files, not JSON.
- The application validates formatting before analysis begins.
- The internal system may convert these files into JSON, but users are not expected to author JSON.
- Required files must be strict enough for repeatable analysis.
- Optional files improve output quality but are not required for the first analysis.

## Required Files

A complete Workflow Packet v1 includes:

```text
workflow_overview.md
workflow_steps.csv
policy_controls.csv
data_dictionary.csv
sample_records.csv