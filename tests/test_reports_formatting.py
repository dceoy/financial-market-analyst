from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

import aims.reports as reports

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_format_generated_markdown_uses_release_cooldown(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    output_path = tmp_path / "report.md"
    output_path.write_text("# Report\n", encoding="utf-8")
    run = mocker.patch.object(reports.subprocess, "run")

    reports._format_generated_markdown(output_path)

    assert run.call_count == 2
    prettier = run.call_args_list[0]
    markdownlint = run.call_args_list[1]
    assert prettier.args[0] == [
        "npx",
        "-y",
        "prettier",
        "--write",
        "--",
        str(output_path),
    ]
    assert markdownlint.args[0][:4] == ["npx", "-y", "markdownlint-cli2", "--fix"]
    for call in run.call_args_list:
        assert call.kwargs["check"] is True
        assert call.kwargs["env"]["NPM_CONFIG_MIN_RELEASE_AGE"] == "7"


@pytest.mark.parametrize(("github_actions", "expected_calls"), [("true", 1), ("false", 0)])
def test_generate_and_save_formats_only_in_github_actions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
    github_actions: str,
    expected_calls: int,
) -> None:
    artifact = {
        "version": "1.0.0",
        "metadata": {
            "generated_at": "2024-01-01T00:00:00+00:00",
            "git_commit": "deadbeef",
            "data_source": "test",
            "data_freshness": {},
            "scoring_version": "1.0.0",
            "config": {},
        },
        "instruments": [],
    }
    artifact_path = tmp_path / "artifact.json"
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
    formatter = mocker.patch.object(reports, "_format_generated_markdown")
    monkeypatch.setenv("GITHUB_ACTIONS", github_actions)

    output_path = reports.generate_and_save(artifact_path, tmp_path / "results")

    assert formatter.call_count == expected_calls
    if expected_calls:
        formatter.assert_called_once_with(output_path)
