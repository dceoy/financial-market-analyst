from pathlib import Path

workflow = Path('.github/workflows/daily-market-analysis.yml')
text = workflow.read_text()
old = '''          uv run python .agents/skills/market-analysis/scripts/generate_report.py \\
            "${ARGS[@]}"
      - uses: actions/setup-go@b7ad1dad31e06c5925ef5d2fc7ad053ef454303e # v7.0.0
'''
new = '''          uv run python .agents/skills/market-analysis/scripts/generate_report.py \\
            "${ARGS[@]}"
      - name: Format generated Markdown
        if: steps.symbols.outputs.symbols != ''
        run: | # zizmor: ignore[adhoc-packages] uses pinned Markdown tools
          files=()
          while IFS= read -r -d '' file; do
            files+=("$file")
          done < <(
            git ls-files -z --modified --others --exclude-standard -- \\
              '*.md' '*.markdown' '*.mdx'
          )
          if [ "${#files[@]}" -eq 0 ]; then
            exit 0
          fi
          npx -y prettier@3.9.6 --write -- "${files[@]}"
          config="${RUNNER_TEMP}/generated-markdownlint.jsonc"
          printf '%s\\n' '{"config":{"MD013":false,"MD033":false,"MD041":false}}' \\
            > "$config"
          npx -y markdownlint-cli2@0.23.2 --fix --config "$config" -- \\
            "${files[@]}"
      - uses: actions/setup-go@b7ad1dad31e06c5925ef5d2fc7ad053ef454303e # v7.0.0
'''
if old not in text:
    raise SystemExit('target block not found')
workflow.write_text(text.replace(old, new, 1))
Path('.github/workflows/patch-generated-markdown.yml').unlink()
Path('.github/patch_generated_markdown.py').unlink()
