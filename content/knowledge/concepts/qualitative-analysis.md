---
description: How the AI qualitative layer adds grounded, citation-bound interpretation
  around the quantitative signal without becoming a source of numeric truth.
params:
  okf_metadata:
    generated:
      at: '2026-07-27T00:00:00Z'
      by: process:aims-okf-migration
    id: okf/concepts/qualitative-analysis
    sources:
    - id: operations
      resource: https://github.com/dceoy/aims/blob/main/OPERATIONS.md
      title: AIMS operations guide
    - id: qualitative-schema
      resource: https://github.com/dceoy/aims/blob/main/data/schema/qualitative.schema.json
      title: Qualitative analysis schema
    status: stable
  okf_source: concepts/qualitative-analysis.md
  okf_type: concept
tags:
- qualitative
- market-analysis
title: Qualitative Analysis
type: knowledge
---

# Qualitative Analysis

How the AI qualitative layer adds grounded, citation-bound interpretation around the quantitative signal without becoming a source of numeric truth.

## Repository facts

AIMS plans a qualitative layer in which a single daily LLM call reads the day's analysis artifact, committed evidence bundle, and event calendar, and writes a schema-validated `data/qualitative/` artifact. The call is the pipeline's only non-deterministic step; validation, deterministic gates, report rendering, and the Hugo build stay deterministic, and reports without a qualitative artifact are byte-identical to today's.

Claims are machine-checkable by contract: stances and confidence are closed enums, drivers carry structured direction and numeric claims, and every driver cites evidence IDs from the committed bundle. Deterministic gates cross-examine those structured claims against the quantitative features and withhold entries that fail; a stance that merely disagrees with the quantitative signal is legitimate output and is never gated for the disagreement.

The layer is fail-open and staged: without an `ANTHROPIC_API_KEY` secret or on any qualitative failure, the quantitative report publishes unchanged; because analysis pull requests auto-merge without human review, rendering is enabled only after a shadow period meets recorded exit criteria.

## Source-of-truth boundary

AIMS keeps numeric market facts, scores, ranks, dates, risk gates, and data availability in generated artifacts and validated reports. Qualitative artifacts may reference those numbers but never restate them authoritatively and never modify them. This OKF concept captures durable design knowledge only; the operational contract lives in `OPERATIONS.md` §10 and `data/schema/qualitative.schema.json`.

## Related concepts

- [Scoring Methodology](../scoring-methodology/)
- [Report Generation](../report-generation/)
- [Publication Workflow](../publication-workflow/)
