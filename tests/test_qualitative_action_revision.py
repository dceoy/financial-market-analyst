"""Tests for Claude Code Action revision discovery."""

from pathlib import Path

import pytest

from aims import qualitative as q


def test_claude_action_revision_rejects_multiple_revisions(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "uses: anthropics/claude-code-action@" + "a" * 40 + "\n"
        "uses: anthropics/claude-code-action@" + "b" * 40 + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="expected one claude-code-action revision"):
        q._claude_action_revision(workflow)
