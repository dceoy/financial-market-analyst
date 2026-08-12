---
id: okf/concepts/scoring-methodology
title: Scoring Methodology
description: How AIMS treats analysis artifacts, score semantics, ranking outputs, and risk gates as generated numeric facts.
type: concept
tags: [scoring, market-analysis]
generated:
  by: process:aims-okf-migration
  at: 2026-07-27T00:00:00Z
status: stable
sources:
  - id: operations
    resource: https://github.com/dceoy/aims/blob/main/OPERATIONS.md
    title: AIMS operations guide
  - id: analysis-schema
    resource: https://github.com/dceoy/aims/blob/main/data/schema/analysis.schema.json
    title: Market analysis schema
  - id: repository-guidelines
    resource: https://github.com/dceoy/aims/blob/main/AGENTS.md
    title: Repository guidelines
---

## Scoring Methodology

How AIMS treats analysis artifacts, score semantics, ranking outputs, and risk gates as generated numeric facts.

## Repository facts

AIMS computes cross-sectional rankings from daily OHLCV-derived features and produces a composite score from percentile ranks. Risk gates mark unreliable instruments, which remain in output but are ranked below reliable instruments.

OKF concepts may summarize durable methodology, but numeric market facts, scores, ranks, dates, risk gates, and availability remain authoritative only in generated analysis artifacts and validated report outputs.

## Source-of-truth boundary

AIMS keeps numeric market facts, scores, ranks, dates, risk gates, and data availability in generated artifacts and validated reports. This OKF concept captures durable repository knowledge only.

## Related concepts

- [Data Sources](/concepts/data-sources.md)
- [Report Generation](/concepts/report-generation.md)
