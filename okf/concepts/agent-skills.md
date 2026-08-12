---
id: okf/concepts/agent-skills
title: Agent Skills
description: Repository-local Agent Skills that guide AIMS automation, OKF curation, site generation, and PR review.
type: concept
tags: [agents, skills, okf]
generated:
  by: process:aims-okf-migration
  at: 2026-07-27T00:00:00Z
status: stable
sources:
  - id: local-qa-skill
    resource: https://github.com/dceoy/aims/blob/main/.agents/skills/local-qa/SKILL.md
    title: Local QA skill
  - id: market-analysis-skill
    resource: https://github.com/dceoy/aims/blob/main/.agents/skills/market-analysis/SKILL.md
    title: Market analysis skill
  - id: cfd-instruments-skill
    resource: https://github.com/dceoy/aims/blob/main/.agents/skills/update-cfd-instruments/SKILL.md
    title: CFD instrument update skill
  - id: okf-author-skill
    resource: https://github.com/dceoy/aims/blob/main/.agents/skills/aims-okf-author/SKILL.md
    title: AIMS OKF authoring skill
---

## Agent Skills

Repository-local Agent Skills that guide AIMS automation, OKF curation, site generation, and PR review.

## Repository facts

Repository-local Agent Skills describe repeatable workflows for market analysis, CFD instrument updates, local QA, PR feedback triage, and OKF maintenance. The OKF author, curator, site, and PR-review skills point agents at canonical `okf/` edits and generated `content/knowledge/` validation.

Agent workflows must keep generated knowledge separate from canonical OKF and must not invent numeric market facts.

## Source-of-truth boundary

AIMS keeps numeric market facts, scores, ranks, dates, risk gates, and data availability in generated artifacts and validated reports. This OKF concept captures durable repository knowledge only.

## Related concepts

- [Architecture](/concepts/architecture.md)
- [Operational Recovery](/concepts/operational-recovery.md)
