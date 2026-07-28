---
description: Repository-level architecture for the AIMS analysis pipeline, Hugo site,
  OKF source, and generated knowledge pages.
params:
  okf_metadata:
    generated:
      at: '2026-07-27T00:00:00Z'
      by: process:aims-okf-migration
    id: okf/concepts/architecture
    sources:
    - id: repository-guidelines
      resource: https://github.com/dceoy/aims/blob/main/AGENTS.md
      title: Repository guidelines
    - id: repository-readme
      resource: https://github.com/dceoy/aims/blob/main/README.md
      title: AIMS README
    status: stable
  okf_source: concepts/architecture.md
  okf_type: concept
tags:
- architecture
- okf
- hugo
title: AIMS Architecture
type: knowledge
---

# AIMS Architecture

Repository-level architecture for the AIMS analysis pipeline, Hugo site, OKF source, and generated knowledge pages.

## Repository facts

AIMS combines Python automation with a Hugo static site. Python scripts live under `.agents/skills/`, tests live in `tests/`, schemas live under `data/schema/`, and Hugo source content lives under `content/`. Generated static output is written to the ignored `site/` directory.

The OKF layer adds `okf/` as the durable knowledge source while preserving existing source-of-truth boundaries: daily analysis JSON remains under `data/analysis/`, public reports remain under `content/results/`, and `content/knowledge/` is regenerated from OKF.

## Source-of-truth boundary

AIMS keeps numeric market facts, scores, ranks, dates, risk gates, and data availability in generated artifacts and validated reports. This OKF concept captures durable repository knowledge only.

## Related concepts

- [Data Sources](../data-sources/)
- [Report Generation](../report-generation/)
- [Publication Workflow](../publication-workflow/)
