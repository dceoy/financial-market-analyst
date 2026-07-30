#!/usr/bin/env bash

set -euxo pipefail
cd "$(git rev-parse --show-toplevel)"

# Python
uv sync
uv run ruff format .
uv run ruff check --fix .
uv run pyright .
uv run pytest

# Validate CFD instruments CSV
uv run python .agents/skills/update-cfd-instruments/scripts/validate_cfd_instruments.py \
	--input data/cfd_instruments.csv \
	--schema data/schema/cfd_instruments.schema.json

# Markdown (JSON is excluded: Prettier rewrites alter SHA-256 hashes used by
# qualitative input verification for analysis/evidence fixtures and artifacts.)
npx -y prettier --write './**/*.md'

# OKF knowledge shadow content
uv run python tools/okf_hugo_adapter.py --src okf --dst content/knowledge --check

# Hugo
hugo --gc --minify

# Shell scripts
git ls-files -z -- '*.sh' '*.bash' '*.bats' | xargs -0 -t shfmt --write
git ls-files -z -- '*.sh' '*.bash' '*.bats' | xargs -0 -t shellcheck

# GitHub Actions
zizmor --fix=safe .github/workflows
git ls-files -z -- '.github/workflows/*.yml' '.github/workflows/*.yaml' | xargs -0 -t actionlint
git ls-files -z -- '.github/workflows/*.yml' '.github/workflows/*.yaml' | xargs -0 -t yamllint -d '{"extends": "relaxed", "rules": {"line-length": "disable"}}'
checkov --framework=all --output=github_failed_only --directory=.
