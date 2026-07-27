---
id: okf/concepts/data-sources
title: Data Sources
description: Authoritative market and instrument data sources used by AIMS and the boundaries for durable knowledge updates.
type: concept
tags: [data-sources, market-analysis]
generated:
  by: process:aims-okf-migration
  at: 2026-07-27T00:00:00Z
status: stable
sources:
  - id: operations
    resource: OPERATIONS.md
    title: AIMS operations guide
  - id: daily-analysis-workflow
    resource: .github/workflows/daily-market-analysis.yml
    title: Daily market analysis workflow
  - id: cfd-update-workflow
    resource: .github/workflows/update-cfd-instruments.yml
    title: CFD instrument update workflow
---

# Data Sources

Authoritative market and instrument data sources used by AIMS and the boundaries for durable knowledge updates.

## Repository facts

AIMS fetches daily OHLCV history from Yahoo Finance (`yfinance` library, default provider) with Stooq registered as a fallback/alternative provider. The daily workflow derives its symbol universe from `data/mappings/canonical_instrument_mappings.csv` for the configured provider and interval — there is no separate provider symbol list file.

Individual stocks are configured the same way as equity indices and commodities: as rows in `canonical_instrument_mappings.csv` with `asset_class=equity`. Adding a stock row with `provider=yfinance` and `provider_interval=d` is sufficient for the daily workflow to fetch and score it — no separate stock symbol list exists.

The CFD instrument master is a separate data source maintained in `data/cfd_instruments.csv`. It is refreshed by the weekly updater workflow and validated before the daily market analysis workflow runs.

## Source-of-truth boundary

AIMS keeps numeric market facts, scores, ranks, dates, risk gates, and data availability in generated artifacts and validated reports. This OKF concept captures durable repository knowledge only.

## Related concepts

- [Instrument Master](/concepts/instrument-master.md)
- [Scoring Methodology](/concepts/scoring-methodology.md)
