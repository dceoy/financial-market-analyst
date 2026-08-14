from pathlib import Path

reports = Path("src/aims/reports.py")
text = reports.read_text()
text = text.replace(
    "import argparse\nimport json\n",
    "import argparse\nimport json\nimport os\nimport subprocess\nimport tempfile\n",
    1,
)
old = '''def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        value: dict[str, Any] = json.load(fh)
    return value


def generate_and_save(
'''
new = '''def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        value: dict[str, Any] = json.load(fh)
    return value


def _format_generated_markdown(output_path: Path) -> None:
    npm_env = os.environ | {"NPM_CONFIG_MIN_RELEASE_AGE": "7"}
    subprocess.run(
        ["npx", "-y", "prettier", "--write", "--", str(output_path)],
        check=True,
        env=npm_env,
    )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonc", encoding="utf-8", delete=False
    ) as fh:
        fh.write('{"config":{"MD013":false,"MD033":false,"MD041":false}}\\n')
        config_path = Path(fh.name)
    try:
        subprocess.run(
            [
                "npx",
                "-y",
                "markdownlint-cli2",
                "--fix",
                "--config",
                str(config_path),
                "--",
                str(output_path),
            ],
            check=True,
            env=npm_env,
        )
    finally:
        config_path.unlink(missing_ok=True)


def generate_and_save(
'''
if old not in text:
    raise SystemExit("generate_and_save insertion point not found")
text = text.replace(old, new, 1)
old = '''    output_path.write_text(content, encoding="utf-8")
    print(f"Report written to {output_path}")
    return output_path
'''
new = '''    output_path.write_text(content, encoding="utf-8")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        _format_generated_markdown(output_path)
    print(f"Report written to {output_path}")
    return output_path
'''
if old not in text:
    raise SystemExit("output formatting insertion point not found")
reports.write_text(text.replace(old, new, 1))

Path(".agents/skills/market-analysis/scripts/generate_report.py").write_text(
    '''#!/usr/bin/env python3
"""Thin wrapper: generate a Hugo Markdown report from an AIMS analysis artifact."""

from __future__ import annotations

import sys

from aims.reports import generate_report, main, report_filename

__all__ = ["generate_report", "main", "report_filename"]

if __name__ == "__main__":
    sys.exit(main())
'''
)
