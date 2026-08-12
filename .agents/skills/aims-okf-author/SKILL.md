---
name: aims-okf-author
description: Create or update canonical OKF concept documents from repository evidence without inventing numeric market facts.
disable-model-invocation: false
---

# AIMS OKF authoring

Author only `okf/` files first. Use `data/analysis/*.json` for numeric facts and cite generated reports only as publication outputs, not canonical facts. Regenerate `content/knowledge/` with the adapter before finishing.

## AIMS paths and commands

- Canonical OKF source: `okf/`
- Generated Hugo shadow content: `content/knowledge/`
- Daily report output: `content/results/`
- Numeric analysis artifacts: `data/analysis/*.json`
- Generate: `uv run python tools/okf_hugo_adapter.py --src okf --dst content/knowledge --clean`
- Check: `uv run python tools/okf_hugo_adapter.py --src okf --dst content/knowledge --check`
- Build: `hugo --gc --minify`

## Guardrails

- Do not let LLM-authored OKF prose become the source of truth for scores, ranks, dates, prices, risk gates, or data availability.
- Author OKF v0.2 metadata: use `generated: { by, at }`, front matter `sources`, and lifecycle `status` values `draft`, `stable`, or `deprecated`.
- Do not use legacy `timestamp`, structured self-referential `resource` mappings, or body-level `# Citations` sections.
- Do not hand-edit `content/knowledge/`; regenerate it from `okf/`.
- Keep custom code small and deterministic.

## OKF primary references

- Google Cloud announcement: <https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing>
- OKF v0.2 specification: <https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md>
