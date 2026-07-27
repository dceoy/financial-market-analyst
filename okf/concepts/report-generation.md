---
id: okf/concepts/report-generation
title: Report Generation
description: How deterministic JSON analysis artifacts become public Hugo market analysis reports.
type: concept
tags: [reports, hugo, market-analysis]
generated:
  by: process:aims-okf-migration
  at: 2026-07-27T00:00:00Z
status: stable
sources:
  - id: operations
    resource: https://github.com/dceoy/aims/blob/main/OPERATIONS.md
    title: AIMS operations guide
  - id: repository-readme
    resource: https://github.com/dceoy/aims/blob/main/README.md
    title: AIMS README
  - id: report-golden
    resource: https://github.com/dceoy/aims/blob/main/tests/golden/2024-01-01-market-analysis.md
    title: Market analysis report golden
---

# Report Generation

How deterministic JSON analysis artifacts become public Hugo market analysis reports.

## Repository facts

The report generator reads `data/analysis/YYYY-MM-DD.json` and writes Hugo Markdown reports to `content/results/YYYY-MM-DD-market-analysis.md`. The generator is deterministic: identical JSON input produces identical Markdown output and the report timestamp comes from the artifact.

OKF-generated `content/knowledge/` pages are separate from `content/results/` reports and do not replace daily report generation.

## Source-of-truth boundary

AIMS keeps numeric market facts, scores, ranks, dates, risk gates, and data availability in generated artifacts and validated reports. This OKF concept captures durable repository knowledge only.

## Related concepts

- [Architecture](/concepts/architecture.md)
- [Publication Workflow](/concepts/publication-workflow.md)
