---
id: okf/concepts/instrument-master
title: Instrument Master
description: Canonical CFD instrument reference data and validation responsibilities in AIMS.
type: concept
tags: [cfd, data, instrument-master]
generated:
  by: process:aims-okf-migration
  at: 2026-07-27T00:00:00Z
status: stable
sources:
  - id: operations
    resource: OPERATIONS.md
    title: AIMS operations guide
  - id: cfd-schema
    resource: data/schema/cfd_instruments.schema.json
    title: CFD instrument schema
  - id: cfd-instruments-skill
    resource: .agents/skills/update-cfd-instruments/SKILL.md
    title: CFD instrument update skill
---

# Instrument Master

Canonical CFD instrument reference data and validation responsibilities in AIMS.

## Repository facts

The CFD instrument master is stored in `data/cfd_instruments.csv` and sourced from GMO Click Securities and Rakuten Securities CFD lineup pages. Broker ticker symbols are maintained separately from Stooq symbols, with mappings in `data/mappings/cfd_ticker_mappings.csv`.

The master CSV is validated against `data/schema/cfd_instruments.schema.json` after updates and before daily analysis.

## Source-of-truth boundary

AIMS keeps numeric market facts, scores, ranks, dates, risk gates, and data availability in generated artifacts and validated reports. This OKF concept captures durable repository knowledge only.

## Related concepts

- [Data Sources](/concepts/data-sources.md)
- [Scoring Methodology](/concepts/scoring-methodology.md)
