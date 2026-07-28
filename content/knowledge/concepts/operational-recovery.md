---
description: Runbook-oriented knowledge for restoring AIMS analysis, validation, and
  publication workflows.
params:
  okf_metadata:
    generated:
      at: '2026-07-27T00:00:00Z'
      by: process:aims-okf-migration
    id: okf/concepts/operational-recovery
    sources:
    - id: operations
      resource: https://github.com/dceoy/aims/blob/main/OPERATIONS.md
      title: AIMS operations guide
    - id: local-qa-skill
      resource: https://github.com/dceoy/aims/blob/main/.agents/skills/local-qa/SKILL.md
      title: Local QA skill
    status: stable
  okf_source: concepts/operational-recovery.md
  okf_type: concept
tags:
- operations
- recovery
title: Operational Recovery
type: knowledge
---

# Operational Recovery

Runbook-oriented knowledge for restoring AIMS analysis, validation, and publication workflows.

## Repository facts

Operational recovery starts from the failing workflow step: Stooq fetch warnings are non-fatal per symbol, artifact validation failures should be fixed in the generated JSON or generator inputs, and site build failures should be reproduced locally with Hugo.

Manual recovery uses the documented scripts and validations rather than editing generated outputs by hand.

## Source-of-truth boundary

AIMS keeps numeric market facts, scores, ranks, dates, risk gates, and data availability in generated artifacts and validated reports. This OKF concept captures durable repository knowledge only.

## Related concepts

- [Publication Workflow](../publication-workflow/)
- [Agent Skills](../agent-skills/)
