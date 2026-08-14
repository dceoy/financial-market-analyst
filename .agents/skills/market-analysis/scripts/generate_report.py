#!/usr/bin/env python3
"""Thin wrapper: generate and format a Hugo Markdown analysis report."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from aims.reports import generate_report, main, parse_args, report_filename

__all__ = ["generate_report", "main", "report_filename"]


def _format_generated_markdown() -> None:
    args = parse_args()
    artifact = json.loads(args.input.read_text(encoding="utf-8"))
    output_path = args.output / report_filename(artifact)
    subprocess.run(
        ["npx", "-y", "prettier@3.9.6", "--write", "--", str(output_path)],
        check=True,
    )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonc", encoding="utf-8", delete=False
    ) as fh:
        fh.write('{"config":{"MD013":false,"MD033":false,"MD041":false}}\n')
        config_path = Path(fh.name)
    try:
        subprocess.run(
            [
                "npx",
                "-y",
                "markdownlint-cli2@0.23.2",
                "--fix",
                "--config",
                str(config_path),
                "--",
                str(output_path),
            ],
            check=True,
        )
    finally:
        config_path.unlink(missing_ok=True)


if __name__ == "__main__":
    exit_code = main()
    if exit_code == 0 and os.environ.get("GITHUB_ACTIONS") == "true":
        _format_generated_markdown()
    sys.exit(exit_code)
