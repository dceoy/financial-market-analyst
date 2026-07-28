import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
import yaml

import aims.okf_hugo as okf_hugo_adapter


def write_concept(path: Path, body: str = "# Concept\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "id: okf/concepts/concept\n"
        "title: Concept\n"
        "description: Test concept\n"
        "type: concept\n"
        "tags: [sales]\n"
        "resource: repository://concepts/concept\n"
        "generated:\n"
        "  by: process:test-suite\n"
        "  at: 2026-06-16T00:00:00Z\n"
        "status: stable\n"
        "sources:\n"
        "  - id: fixture\n"
        "    resource: tests/fixtures/concept.md\n"
        "    title: Concept fixture\n"
        "url: /unsafe\n"
        "slug: unsafe-slug\n"
        "layout: unsafe-layout\n"
        "draft: true\n"
        "weight: 99\n"
        "unknown_key:\n"
        "  nested: preserved\n"
        "---\n"
        f"{body}",
        encoding="utf-8",
    )


def generated_metadata(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    front_matter = text.split("---\n", 2)[1]
    metadata = yaml.safe_load(front_matter)
    assert isinstance(metadata, dict)
    return metadata


def test_adapter_accepts_reserved_files_without_frontmatter(tmp_path: Path) -> None:
    src = tmp_path / "okf"
    dst = tmp_path / "content" / "knowledge"
    src.mkdir()
    (src / "index.md").write_text(
        "# Knowledge\n\n- [Concept](/concepts/concept.md)\n", encoding="utf-8"
    )
    logs = src / "logs"
    logs.mkdir()
    (logs / "log.md").write_text(
        "# Log\n\n## 2026-06-16\n\n- Created.\n", encoding="utf-8"
    )
    write_concept(src / "concepts" / "concept.md")

    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst)]) == 0

    metadata = generated_metadata(dst / "_index.md")
    text = (dst / "_index.md").read_text(encoding="utf-8")
    assert metadata["type"] == "knowledge"
    assert metadata["params"]["okf_reserved"] == "index"
    assert metadata["params"]["okf_source"] == "index.md"
    assert "# Knowledge" in text
    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst), "--check"]) == 0


def test_hugo_metadata_isolates_unknown_and_sensitive_okf_fields(
    tmp_path: Path,
) -> None:
    src = tmp_path / "okf"
    dst = tmp_path / "content" / "knowledge"
    src.mkdir()
    (src / "index.md").write_text(
        '---\nokf_version: "0.2"\n---\n# Knowledge\n', encoding="utf-8"
    )
    write_concept(src / "concepts" / "concept.md")

    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst)]) == 0

    metadata = generated_metadata(dst / "concepts" / "concept.md")
    assert metadata["type"] == "knowledge"
    assert metadata["params"]["okf_type"] == "concept"
    assert metadata["params"]["okf_source"] == "concepts/concept.md"
    assert metadata["tags"] == ["sales"]
    assert metadata["resource"] == "repository://concepts/concept"
    for key in ["id", "status", "url", "slug", "layout", "draft", "weight"]:
        assert key not in metadata
        assert key in metadata["params"]["okf_metadata"]
    assert metadata["params"]["okf_metadata"]["generated"] == {
        "at": "2026-06-16T00:00:00Z",
        "by": "process:test-suite",
    }
    assert metadata["params"]["okf_metadata"]["sources"] == [
        {
            "id": "fixture",
            "resource": "tests/fixtures/concept.md",
            "title": "Concept fixture",
        }
    ]
    assert metadata["params"]["okf_metadata"]["unknown_key"] == {"nested": "preserved"}
    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst), "--check"]) == 0


def test_check_labels_okf_and_aims_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "okf"
    dst = tmp_path / "content" / "knowledge"
    concepts = src / "concepts"
    concepts.mkdir(parents=True)
    (src / "index.md").write_text(
        "---\ntitle: Not allowed\n---\n# Knowledge\n", encoding="utf-8"
    )
    (concepts / "broken.md").write_text(
        "---\n"
        "title: Broken\n"
        "description: Broken concept\n"
        "type: ''\n"
        "tags: [bad_tag]\n"
        "generated: {by: invalid, at: nope}\n"
        "---\n"
        "[Missing](./missing.md)\n",
        encoding="utf-8",
    )

    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst), "--check"]) == 1
    captured = capsys.readouterr().err
    assert "OKF conformance error:" in captured
    assert "AIMS policy error:" in captured


def test_bundle_absolute_links_are_validated(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "okf"
    dst = tmp_path / "content" / "knowledge"
    src.mkdir()
    (src / "index.md").write_text("# Knowledge\n", encoding="utf-8")
    write_concept(src / "concepts" / "foo.md", "# Foo\n[Foo](/concepts/foo.md)\n")

    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst)]) == 0
    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst), "--check"]) == 0

    write_concept(
        src / "concepts" / "foo.md", "# Foo\n[Broken](/concepts/missing.md)\n"
    )
    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst), "--check"]) == 1
    assert "broken link '/concepts/missing.md'" in capsys.readouterr().err


def test_internal_links_rewrite_to_hugo_urls(tmp_path: Path) -> None:
    src = tmp_path / "okf"
    dst = tmp_path / "content" / "knowledge"
    src.mkdir()
    (src / "index.md").write_text("# Knowledge\n", encoding="utf-8")
    (src / "areas").mkdir()
    (src / "areas" / "index.md").write_text("# Area Index\n", encoding="utf-8")
    write_concept(src / "concepts" / "bar.md", "# Bar\n")
    write_concept(
        src / "concepts" / "foo.md",
        "# Foo\n[Bar](./bar.md)\n[Area](/areas/index.md)\n",
    )

    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst)]) == 0

    generated = (dst / "concepts" / "foo.md").read_text(encoding="utf-8")
    assert "[Bar](../bar/)" in generated
    assert "[Area](../../areas/)" in generated
    assert "./bar.md" not in generated
    assert "/knowledge/" not in generated


def test_knowledge_index_links_are_relative(tmp_path: Path) -> None:
    src = tmp_path / "okf"
    dst = tmp_path / "content" / "knowledge"
    src.mkdir()
    (src / "index.md").write_text(
        "# Knowledge\n\n- [Concept](/concepts/concept.md)\n", encoding="utf-8"
    )
    write_concept(src / "concepts" / "concept.md")

    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst)]) == 0

    generated = (dst / "_index.md").read_text(encoding="utf-8")
    assert "[Concept](concepts/concept/)" in generated
    assert "/knowledge/" not in generated


def test_okf_yaml_loader_does_not_mutate_safe_loader() -> None:
    parsed = yaml.safe_load("value: 2026-06-16T00:00:00Z")
    assert isinstance(parsed, dict)
    assert isinstance(parsed["value"], datetime)


def test_internal_links_preserve_label_when_it_matches_target(tmp_path: Path) -> None:
    src = tmp_path / "okf"
    dst = tmp_path / "content" / "knowledge"
    src.mkdir()
    (src / "index.md").write_text("# Knowledge\n", encoding="utf-8")
    write_concept(src / "concepts" / "bar.md", "# Bar\n")
    write_concept(
        src / "concepts" / "foo.md",
        "# Foo\n[./bar.md](./bar.md)\n",
    )

    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst)]) == 0

    generated = (dst / "concepts" / "foo.md").read_text(encoding="utf-8")
    assert "[./bar.md](../bar/)" in generated


def test_check_detects_generated_drift(tmp_path: Path) -> None:
    src = tmp_path / "okf"
    dst = tmp_path / "content" / "knowledge"
    src.mkdir()
    (src / "index.md").write_text("# Knowledge\n", encoding="utf-8")
    write_concept(src / "concepts" / "concept.md")

    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst)]) == 0
    first = (dst / "concepts" / "concept.md").read_text(encoding="utf-8")
    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst), "--check"]) == 0

    (dst / "concepts" / "concept.md").write_text(f"{first}\n", encoding="utf-8")
    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst), "--check"]) == 1
    assert (
        okf_hugo_adapter.render_document(
            okf_hugo_adapter.load_documents(src, dst)[0][0], src, dst
        )
        == first
    )


def test_parent_directory_links_rewrite_to_hugo_urls(tmp_path: Path) -> None:
    src = tmp_path / "okf"
    dst = tmp_path / "content" / "knowledge"
    src.mkdir()
    (src / "index.md").write_text("# Knowledge\n", encoding="utf-8")
    logs = src / "logs"
    logs.mkdir()
    (logs / "log.md").write_text("# Log\n", encoding="utf-8")
    write_concept(
        src / "concepts" / "foo.md",
        "# Foo\n[Index](../index.md)\n[Log](../logs/log.md)\n",
    )

    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst)]) == 0

    generated = (dst / "concepts" / "foo.md").read_text(encoding="utf-8")
    assert "[Index](../../)" in generated
    assert "[Log](../../logs/log/)" in generated
    assert "../index.md" not in generated
    assert "../logs/log.md" not in generated
    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst), "--check"]) == 0


def test_check_rejects_internal_links_that_escape_okf_bundle(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "okf"
    dst = tmp_path / "content" / "knowledge"
    outside = tmp_path / "outside.md"
    outside.write_text("# Outside\n", encoding="utf-8")
    src.mkdir()
    (src / "index.md").write_text("# Knowledge\n", encoding="utf-8")
    write_concept(src / "concepts" / "foo.md", "# Foo\n[Outside](../../outside.md)\n")

    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst), "--check"]) == 1
    captured = capsys.readouterr().err
    assert "unsafe internal link '../../outside.md' escapes OKF bundle" in captured


def test_okf_hugo_adapter_tool_help_exits_successfully() -> None:
    result = subprocess.run(
        [sys.executable, "tools/okf_hugo_adapter.py", "--help"],
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0


def test_split_front_matter_null_yaml_yields_empty_metadata(tmp_path: Path) -> None:
    f = tmp_path / "null.md"
    f.write_text("---\n\n---\nbody text\n", encoding="utf-8")
    metadata, body, has_fm = okf_hugo_adapter.split_front_matter(f)
    assert metadata == {}
    assert "body text" in body
    assert has_fm is True


def test_split_front_matter_non_dict_raises(tmp_path: Path) -> None:
    f = tmp_path / "list.md"
    f.write_text("---\n- item1\n- item2\n---\nbody\n", encoding="utf-8")
    with pytest.raises(TypeError, match="front matter must be a YAML mapping"):
        okf_hugo_adapter.split_front_matter(f)


def test_load_documents_captures_yaml_error(tmp_path: Path) -> None:
    src = tmp_path / "okf"
    src.mkdir()
    (src / "bad.md").write_text("---\n{invalid:\n---\nbody\n", encoding="utf-8")
    docs, errors = okf_hugo_adapter.load_documents(src, tmp_path / "dst")
    assert docs == []
    assert any("YAML front matter does not parse" in e for e in errors)


def test_load_documents_captures_type_error(tmp_path: Path) -> None:
    src = tmp_path / "okf"
    src.mkdir()
    (src / "bad.md").write_text("---\n- item\n---\nbody\n", encoding="utf-8")
    docs, errors = okf_hugo_adapter.load_documents(src, tmp_path / "dst")
    assert docs == []
    assert any("front matter must be a YAML mapping" in e for e in errors)


def test_split_link_target_with_anchor() -> None:
    path_part, suffix = okf_hugo_adapter.split_link_target("./bar.md#section")
    assert path_part == "./bar.md"
    assert suffix == "#section"


def test_hugo_body_preserves_pending_links(tmp_path: Path) -> None:
    src = tmp_path / "okf"
    dst = tmp_path / "dst"
    src.mkdir()
    write_concept(src / "concepts" / "foo.md", "# Foo\n[Pending](./bar.md#pending)\n")
    docs, _ = okf_hugo_adapter.load_documents(src, dst)
    body = okf_hugo_adapter.hugo_body(docs[0], src, dst)
    assert "./bar.md#pending" in body


def test_write_documents_clean_removes_dst(tmp_path: Path) -> None:
    src = tmp_path / "okf"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "index.md").write_text("# Knowledge\n", encoding="utf-8")
    write_concept(src / "concepts" / "c.md")
    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst)]) == 0
    stale = dst / "stale.md"
    stale.write_text("stale", encoding="utf-8")
    assert stale.exists()
    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst), "--clean"]) == 0
    assert not stale.exists()


def test_validate_documents_reports_missing_bundle_index(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "okf"
    dst = tmp_path / "dst"
    src.mkdir()
    write_concept(src / "concepts" / "c.md")
    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst), "--check"]) == 1
    assert "bundle index is missing" in capsys.readouterr().err


def test_validate_concept_without_front_matter(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "okf"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "index.md").write_text("# Knowledge\n", encoding="utf-8")
    (src / "concepts").mkdir()
    (src / "concepts" / "c.md").write_text("# No front matter\n", encoding="utf-8")
    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst), "--check"]) == 1
    assert "concept requires YAML front matter" in capsys.readouterr().err


def test_validate_concept_rejects_non_string_type_list(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "okf"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "index.md").write_text("# Knowledge\n", encoding="utf-8")
    (src / "concepts").mkdir()
    (src / "concepts" / "c.md").write_text(
        "---\ntitle: C\ntype: [concept]\n---\n# C\n", encoding="utf-8"
    )
    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst), "--check"]) == 1
    assert "concept requires non-empty 'type'" in capsys.readouterr().err


def test_validate_concept_rejects_non_string_type_mapping(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "okf"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "index.md").write_text("# Knowledge\n", encoding="utf-8")
    (src / "concepts").mkdir()
    (src / "concepts" / "c.md").write_text(
        "---\ntitle: C\ntype: {name: concept}\n---\n# C\n", encoding="utf-8"
    )
    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst), "--check"]) == 1
    assert "concept requires non-empty 'type'" in capsys.readouterr().err


def test_validate_reserved_log_with_front_matter(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "okf"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "index.md").write_text("# Knowledge\n", encoding="utf-8")
    logs = src / "logs"
    logs.mkdir()
    (logs / "log.md").write_text("---\ntitle: Bad\n---\n# Log\n", encoding="utf-8")
    write_concept(src / "concepts" / "c.md")
    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst), "--check"]) == 1
    assert (
        "reserved log.md must not have concept front matter" in capsys.readouterr().err
    )


def test_validate_aims_policy_empty_tags(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "okf"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "index.md").write_text("# Knowledge\n", encoding="utf-8")
    (src / "concepts").mkdir()
    (src / "concepts" / "c.md").write_text(
        "---\n"
        "title: C\n"
        "description: Desc\n"
        "type: concept\n"
        "tags: []\n"
        "generated: {by: process:test-suite, at: 2026-01-01T00:00:00Z}\n"
        "---\n"
        "# C\n",
        encoding="utf-8",
    )
    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst), "--check"]) == 1
    assert "tags should be a non-empty list" in capsys.readouterr().err


def test_validate_aims_policy_missing_sources(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "okf"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "index.md").write_text("# Knowledge\n", encoding="utf-8")
    (src / "concepts").mkdir()
    (src / "concepts" / "c.md").write_text(
        "---\n"
        "title: C\n"
        "description: Desc\n"
        "type: concept\n"
        "tags: [sales]\n"
        "generated: {by: process:test-suite, at: 2026-01-01T00:00:00Z}\n"
        "---\n"
        "# C\n",
        encoding="utf-8",
    )
    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst), "--check"]) == 1
    assert "recommended field 'sources' is missing" in capsys.readouterr().err


def test_validate_links_skips_external_and_mailto(tmp_path: Path) -> None:
    src = tmp_path / "okf"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "index.md").write_text("# Knowledge\n", encoding="utf-8")
    write_concept(
        src / "concepts" / "c.md",
        "# C\n[Ext](https://example.com)\n[Mail](mailto:foo@bar.com)\n",
    )
    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst)]) == 0
    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst), "--check"]) == 0


def test_main_parse_errors_in_write_mode(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    src = tmp_path / "okf"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "bad.md").write_text("---\n{invalid:\n---\nbody\n", encoding="utf-8")
    assert okf_hugo_adapter.main(["--src", str(src), "--dst", str(dst)]) == 1
    assert "YAML front matter does not parse" in capsys.readouterr().err


def validation_document(
    tmp_path: Path, metadata: dict[str, Any], body: str = "# Concept\n"
) -> okf_hugo_adapter.OkfDocument:
    source = tmp_path / "okf" / "concepts" / "concept.md"
    return okf_hugo_adapter.OkfDocument(
        source=source,
        destination=tmp_path / "content" / "knowledge" / "concepts" / "concept.md",
        metadata=metadata,
        body=body,
        reserved=False,
        has_front_matter=True,
    )


def test_validate_v02_accepts_all_standard_metadata(tmp_path: Path) -> None:
    metadata: dict[str, Any] = {
        "type": "Attested Computation",
        "resource": "references/computations/example.sql",
        "status": "draft",
        "generated": {
            "by": "process:test-suite",
            "at": "2026-07-27T00:00:00Z",
        },
        "verified": {
            "by": "human:reviewer",
            "at": "2026-07-27T01:00:00Z",
        },
        "stale_after": "2026-12-31",
        "sources": [
            {
                "id": "policy",
                "resource": "references/policy.md",
                "title": "Policy",
                "author": "team:docs",
                "usage_count": 0,
                "last_modified": "2026-07-26",
                "usage_window": {"from": "2026-07-01", "to": "2026-07-27"},
            }
        ],
        "usage_window": {"from": "2026-07-01", "to": "2026-07-27"},
        "runtime": "python",
        "parameters": [{"name": "value", "type": "integer", "required": True}],
        "computation": "references/computations/example.py",
        "executor": {
            "resource": "references/executors/python.md",
            "receipt": ["result"],
        },
        "attester": {"resource": "references/attesters/example.py"},
        "extension": {"preserved": True},
    }
    document = validation_document(tmp_path, metadata)
    assert okf_hugo_adapter.validate_v02_metadata(document) == []


@pytest.mark.parametrize(
    ("metadata", "body", "expected"),
    [
        (
            {"type": "concept", "timestamp": "2026-01-01T00:00:00Z"},
            "# Citations\n",
            ["legacy 'timestamp'", "body-level '# Citations'"],
        ),
        (
            {
                "type": "concept",
                "resource": {},
                "status": "seeded",
                "generated": "invalid",
                "stale_after": "2026-02-30",
                "sources": "invalid",
                "usage_window": "invalid",
                "computation": "",
                "parameters": "invalid",
                "executor": "invalid",
                "attester": "invalid",
            },
            "# Concept\n",
            [
                "'resource'",
                "'status'",
                "'generated' must be a mapping",
                "'stale_after'",
                "'sources' must be a list",
                "'usage_window' must be a mapping",
                "'computation'",
                "'parameters' must be a list",
                "'executor' must be a mapping",
                "'attester' must be a mapping",
            ],
        ),
        (
            {
                "type": "Attested Computation",
                "generated": {"by": "invalid", "at": "2026-99-99T00:00:00Z"},
                "verified": [
                    "invalid",
                    {"by": "", "at": "2026-07-27"},
                ],
                "stale_after": "2026-13-01",
                "sources": [
                    "invalid",
                    {
                        "resource": "",
                        "id": "",
                        "title": 1,
                        "author": "invalid",
                        "usage_count": True,
                        "last_modified": "2026-13-01",
                        "usage_window": {
                            "from": "2026-02-30",
                            "to": "invalid",
                        },
                    },
                ],
                "usage_window": {"from": None, "to": "2026-02-30"},
                "parameters": [
                    "invalid",
                    {"name": "", "type": None, "required": "yes"},
                ],
                "executor": {"resource": "", "receipt": [""]},
                "attester": {},
            },
            "# Concept\n",
            [
                "'generated.by'",
                "'generated.at'",
                "'verified[0]' must be a mapping",
                "'verified[1].by'",
                "'verified[1].at'",
                "'sources[0]' must be a mapping",
                "'sources[1].resource'",
                "'sources[1].usage_count'",
                "'parameters[0]' must be a mapping",
                "'parameters[1].required'",
                "'executor.receipt'",
                "'attester.resource'",
                "'runtime' is required",
            ],
        ),
        (
            {"type": "concept", "verified": []},
            "# Concept\n",
            ["'verified' must not be an empty list"],
        ),
        (
            {"type": "concept", "sources": []},
            "# Concept\n",
            ["'sources' must not be an empty list"],
        ),
        (
            {"type": "Attested Computation", "runtime": "python"},
            "# Concept\n",
            ["requires a 'computation' path or a non-empty body"],
        ),
        (
            {"type": "Attested Computation", "runtime": "python"},
            "# Computation\n\n",
            ["requires a 'computation' path or a non-empty body"],
        ),
        (
            {"type": "Attested Computation", "runtime": "python"},
            "# Computation\n```python\n\n```\n",
            ["requires a 'computation' path or a non-empty body"],
        ),
        (
            {
                "type": "Attested Computation",
                "runtime": "python",
                "computation": "references/computations/example.py",
            },
            "# Computation\n```python\npass\n```\n",
            ["must not set both a 'computation' path"],
        ),
        (
            {
                "type": "concept",
                "sources": [
                    {"resource": "references/policy.md", "usage_count": 1},
                ],
            },
            "# Concept\n",
            ["'sources[0].usage_count' requires"],
        ),
        (
            {
                "type": "concept",
                "usage_window": {"from": "2026-07-27", "to": "2026-07-01"},
            },
            "# Concept\n",
            ["'usage_window' must satisfy 'from' <= 'to'"],
        ),
        (
            {"type": "concept", "status": ["stable"]},
            "# Concept\n",
            ["'status' must be draft, stable, or deprecated"],
        ),
        (
            {"type": "concept", "status": {"value": "stable"}},
            "# Concept\n",
            ["'status' must be draft, stable, or deprecated"],
        ),
        (
            {"type": "Attested Computation", "runtime": "python"},
            "# Computation\n```python\nfirst()\n```\n```python\nsecond()\n```\n",
            ["must contain exactly one fenced code block"],
        ),
        (
            {"type": "Attested Computation", "runtime": "python"},
            (
                "# Computation\n```python\nfirst()\n```\nSome explanation.\n"
                "```python\nsecond()\n```\n"
            ),
            ["must contain exactly one fenced code block"],
        ),
        (
            {"type": "Attested Computation", "runtime": "python"},
            (
                "# Computation\n```python\nfirst()\n```\n"
                "# Notes\nSome other content.\n"
                "# Computation\n```python\nsecond()\n```\n"
            ),
            ["must contain exactly one fenced code block"],
        ),
    ],
)
def test_validate_v02_rejects_invalid_metadata(
    tmp_path: Path,
    metadata: dict[str, Any],
    body: str,
    expected: list[str],
) -> None:
    document = validation_document(tmp_path, metadata, body)
    errors = okf_hugo_adapter.validate_v02_metadata(document)
    for fragment in expected:
        assert any(fragment in error for error in errors)


def test_validate_v02_accepts_inline_computation_body(tmp_path: Path) -> None:
    metadata: dict[str, Any] = {
        "type": "Attested Computation",
        "runtime": "python",
    }
    body = "# Computation\n```python\npass\n```\n"
    document = validation_document(tmp_path, metadata, body)
    assert okf_hugo_adapter.validate_v02_metadata(document) == []


def test_validate_v02_accepts_shell_comment_lines_inside_computation_fence(
    tmp_path: Path,
) -> None:
    metadata: dict[str, Any] = {
        "type": "Attested Computation",
        "runtime": "bash",
    }
    body = "# Computation\n```bash\n# install deps\nmake build\n```\n"
    document = validation_document(tmp_path, metadata, body)
    assert okf_hugo_adapter.validate_v02_metadata(document) == []


def test_validate_v02_ignores_fenced_blocks_after_next_heading(
    tmp_path: Path,
) -> None:
    metadata: dict[str, Any] = {
        "type": "Attested Computation",
        "runtime": "python",
    }
    body = (
        "# Computation\n```python\npass\n```\n"
        "# Notes\nSome other content.\n```python\nignored()\n```\n"
    )
    document = validation_document(tmp_path, metadata, body)
    assert okf_hugo_adapter.validate_v02_metadata(document) == []


def test_validate_v02_ignores_computation_heading_inside_unrelated_fence(
    tmp_path: Path,
) -> None:
    metadata: dict[str, Any] = {
        "type": "Attested Computation",
        "runtime": "python",
    }
    body = (
        "# Notes\n```text\nExample heading:\n# Computation\n```\n"
        "# Computation\n```python\nreal()\n```\n"
    )
    document = validation_document(tmp_path, metadata, body)
    assert okf_hugo_adapter.validate_v02_metadata(document) == []


def test_validate_v02_accepts_tilde_fenced_computation_body(
    tmp_path: Path,
) -> None:
    metadata: dict[str, Any] = {
        "type": "Attested Computation",
        "runtime": "python",
    }
    body = "# Computation\n~~~python\npass\n~~~\n"
    document = validation_document(tmp_path, metadata, body)
    assert okf_hugo_adapter.validate_v02_metadata(document) == []


def test_validate_v02_accepts_indented_fenced_computation_body(
    tmp_path: Path,
) -> None:
    metadata: dict[str, Any] = {
        "type": "Attested Computation",
        "runtime": "python",
    }
    body = "# Computation\n   ```python\n   pass\n   ```\n"
    document = validation_document(tmp_path, metadata, body)
    assert okf_hugo_adapter.validate_v02_metadata(document) == []


def test_validate_v02_accepts_usage_count_with_document_level_window(
    tmp_path: Path,
) -> None:
    metadata: dict[str, Any] = {
        "type": "concept",
        "sources": [{"resource": "references/policy.md", "usage_count": 1}],
        "usage_window": {"from": "2026-07-01", "to": "2026-07-27"},
    }
    document = validation_document(tmp_path, metadata)
    assert okf_hugo_adapter.validate_v02_metadata(document) == []
