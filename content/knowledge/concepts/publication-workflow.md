---
description: How CI/CD, pull requests, and GitHub Pages publish AIMS reports and generated
  OKF shadow content.
params:
  okf_metadata:
    generated:
      at: '2026-07-27T00:00:00Z'
      by: process:aims-okf-migration
    id: okf/concepts/publication-workflow
    sources:
    - id: operations
      resource: https://github.com/dceoy/aims/blob/main/OPERATIONS.md
      title: AIMS operations guide
    - id: daily-analysis-workflow
      resource: https://github.com/dceoy/aims/blob/main/.github/workflows/daily-market-analysis.yml
      title: Daily market analysis workflow
    - id: ci-workflow
      resource: https://github.com/dceoy/aims/blob/main/.github/workflows/ci.yml
      title: Continuous integration workflow
    status: stable
  okf_source: concepts/publication-workflow.md
  okf_type: concept
tags:
- ci
- hugo
- publication
title: Publication Workflow
type: knowledge
---

## Publication Workflow

How CI/CD, pull requests, and GitHub Pages publish AIMS reports and generated OKF shadow content.

## Repository facts

The daily analysis workflow validates the CFD master, generates JSON artifacts, validates the artifact, generates a Hugo report, builds the Hugo site for validation, and opens a pull request for review.

The CI workflow deploys the Hugo site to GitHub Pages after linting, type checking, and tests pass. The OKF validation job checks generated knowledge content drift before deployment.

## Source-of-truth boundary

AIMS keeps numeric market facts, scores, ranks, dates, risk gates, and data availability in generated artifacts and validated reports. This OKF concept captures durable repository knowledge only.

## Related concepts

- [Architecture](../architecture/)
- [Operational Recovery](../operational-recovery/)
