"""Generate and validate Hugo shadow content from AIMS OKF Markdown."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml


class OkfYamlLoader(yaml.SafeLoader):
    """YAML loader that leaves OKF scalar values such as timestamps as strings."""


OkfYamlLoader.yaml_implicit_resolvers = {
    first_character: list(resolvers)
    for first_character, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
for first_character, resolvers in list(OkfYamlLoader.yaml_implicit_resolvers.items()):
    OkfYamlLoader.yaml_implicit_resolvers[first_character] = [
        (tag, regexp)
        for tag, regexp in resolvers
        if tag != "tag:yaml.org,2002:timestamp"
    ]


FRONT_MATTER = re.compile(r"\A---\n(?P<meta>.*?)\n---\n(?P<body>.*)\Z", re.DOTALL)
LINK = re.compile(r"(?<!!)\[(?P<label>[^\]]+)\]\((?P<target>[^)]+)\)")
TAG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ACTOR = re.compile(r"^(?:[a-z][a-z0-9-]*:[^\s:]+|[^/\s]+/[^/\s]+)$")
CITATIONS_HEADING = re.compile(r"(?m)^# Citations\s*$")
COMPUTATION_HEADING_LINE = re.compile(r"^# Computation\s*$")
HEADING_LINE = re.compile(r"^#[ \t]")
FENCE_LINE = re.compile(r"^ {0,3}(?P<marker>`{3,}|~{3,})")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RECOMMENDED_CONCEPT_FIELDS = ("title", "description", "tags", "generated", "sources")
ROOT_INDEX_ALLOWED_FIELDS = {"okf_version"}
RESERVED_NAMES = {"index.md", "log.md"}
HUGO_TOP_LEVEL_KEYS = {"title", "description", "tags", "resource"}
LIFECYCLE_STATUSES = {"draft", "stable", "deprecated"}


@dataclass(frozen=True)
class OkfDocument:
    """Parsed OKF Markdown document."""

    source: Path
    destination: Path
    metadata: dict[str, Any]
    body: str
    reserved: bool
    has_front_matter: bool


def split_front_matter(path: Path) -> tuple[dict[str, Any], str, bool]:
    """Split optional YAML front matter from an OKF Markdown file."""
    text = path.read_text(encoding="utf-8")
    match = FRONT_MATTER.match(text)
    if match is None:
        return {}, text, False
    metadata = yaml.load(match.group("meta"), Loader=OkfYamlLoader)  # noqa: S506
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        msg = f"OKF conformance error: {path}: front matter must be a YAML mapping"
        raise TypeError(msg)
    return metadata, match.group("body"), True


def dump_yaml(metadata: dict[str, Any]) -> str:
    """Serialize metadata deterministically for Hugo front matter."""
    return yaml.safe_dump(
        metadata,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=True,
    )


def destination_for(source: Path, src_root: Path, dst_root: Path) -> Path:
    """Return the Hugo destination path for an OKF Markdown source path."""
    relative = source.resolve().relative_to(src_root.resolve())
    if relative.name == "index.md":
        relative = relative.with_name("_index.md")
    return dst_root / relative


def iter_markdown(root: Path) -> list[Path]:
    """List Markdown files below a root in stable order."""
    return sorted(path for path in root.rglob("*.md") if path.is_file())


def is_reserved(path: Path) -> bool:
    """Return whether an OKF Markdown path is reserved by OKF v0.2."""
    return path.name in RESERVED_NAMES


def load_documents(
    src_root: Path, dst_root: Path
) -> tuple[list[OkfDocument], list[str]]:
    """Load OKF documents from source root and capture parse errors."""
    documents: list[OkfDocument] = []
    errors: list[str] = []
    for source in iter_markdown(src_root):
        try:
            metadata, body, has_front_matter = split_front_matter(source)
        except yaml.YAMLError as exc:
            errors.append(
                "OKF conformance error: "
                f"{source}: YAML front matter does not parse: {exc}"
            )
            continue
        except (TypeError, ValueError) as exc:
            errors.append(str(exc))
            continue
        documents.append(
            OkfDocument(
                source=source,
                destination=destination_for(source, src_root, dst_root),
                metadata=metadata,
                body=body,
                reserved=is_reserved(source),
                has_front_matter=has_front_matter,
            )
        )
    return documents, errors


def heading_title(body: str, fallback: str) -> str:
    """Extract a title from the first Markdown H1 or use a fallback."""
    for line in body.splitlines():
        if line.startswith("# "):
            return line.removeprefix("# ").strip()
    return fallback


def hugo_metadata(document: OkfDocument, src_root: Path) -> dict[str, Any]:
    """Map OKF metadata to Hugo-safe metadata."""
    converted = {
        key: value
        for key, value in document.metadata.items()
        if key in HUGO_TOP_LEVEL_KEYS
    }
    okf_metadata = {
        key: value
        for key, value in document.metadata.items()
        if key not in HUGO_TOP_LEVEL_KEYS and key != "type"
    }
    params: dict[str, Any] = {}
    okf_type = document.metadata.get("type")
    if okf_type is not None:
        params["okf_type"] = okf_type
    if okf_metadata:
        params["okf_metadata"] = okf_metadata
    params["okf_source"] = str(document.source.relative_to(src_root))
    if document.reserved:
        params["okf_reserved"] = document.source.name.removesuffix(".md")
    converted["params"] = params
    converted["type"] = "knowledge"
    converted.setdefault(
        "title", heading_title(document.body, document.source.stem.title())
    )
    converted.setdefault(
        "description", f"Generated from {document.source.relative_to(src_root)}."
    )
    return converted


def page_url_parts(destination: Path, dst_root: Path) -> tuple[str, ...]:
    """Return URL directory components for a Hugo destination file."""
    relative = destination.relative_to(dst_root)
    if relative.name == "_index.md":
        return tuple(relative.parent.parts) if relative.parent != Path() else ()
    return tuple(relative.with_suffix("").parts)


def relative_hugo_link(
    from_destination: Path, to_destination: Path, dst_root: Path
) -> str:
    """Return a baseURL-safe relative link between two Hugo destination files."""
    from_parts = page_url_parts(from_destination, dst_root)
    to_parts = page_url_parts(to_destination, dst_root)
    common = 0
    for left, right in zip(from_parts, to_parts, strict=False):
        if left != right:
            break
        common += 1
    up = len(from_parts) - common
    down = to_parts[common:]
    path = "/".join(down) if up == 0 else "/".join([".."] * up + list(down))
    return f"{path}/" if path else "./"


def split_link_target(target: str) -> tuple[str, str]:
    """Split a Markdown link target into path and suffix components."""
    separators = [
        index for index in (target.find("?"), target.find("#")) if index != -1
    ]
    if not separators:
        return target, ""
    split_at = min(separators)
    return target[:split_at], target[split_at:]


def resolve_internal_okf_target(
    document: OkfDocument, target_path: str, src_root: Path
) -> Path | None:
    """Resolve an internal OKF link target to an absolute path inside the bundle."""
    if target_path.startswith("/"):
        okf_path = src_root / target_path.removeprefix("/")
    else:
        okf_path = document.source.parent / target_path
    resolved = okf_path.resolve()
    src_resolved = src_root.resolve()
    if not resolved.is_relative_to(src_resolved):
        return None
    return resolved


def hugo_body(document: OkfDocument, src_root: Path, dst_root: Path) -> str:
    """Rewrite OKF internal Markdown links for Hugo knowledge URLs."""

    def replace(match: re.Match[str]) -> str:
        target = match.group("target")
        target_path, suffix = split_link_target(target)
        if (
            not target_path
            or "://" in target_path
            or target_path.startswith("mailto:")
            or pending_link(target)
        ):
            return match.group(0)
        resolved = resolve_internal_okf_target(document, target_path, src_root)
        if resolved is None or resolved.suffix != ".md":
            return match.group(0)
        target_destination = destination_for(resolved, src_root, dst_root)
        rewritten = (
            f"{relative_hugo_link(document.destination, target_destination, dst_root)}"
            f"{suffix}"
        )
        return f"[{match.group('label')}]({rewritten})"

    return LINK.sub(replace, document.body)


def render_document(document: OkfDocument, src_root: Path, dst_root: Path) -> str:
    """Render a Hugo Markdown document from an OKF document."""
    front_matter = dump_yaml(hugo_metadata(document, src_root))
    return f"---\n{front_matter}---\n{hugo_body(document, src_root, dst_root)}"


def write_documents(
    documents: list[OkfDocument], src_root: Path, dst_root: Path, clean: bool
) -> None:
    """Write generated Hugo content to disk."""
    if clean and dst_root.exists():
        shutil.rmtree(dst_root)
    for document in documents:
        document.destination.parent.mkdir(parents=True, exist_ok=True)
        document.destination.write_text(
            render_document(document, src_root, dst_root), encoding="utf-8"
        )


def validate_documents(
    documents: list[OkfDocument],
    parse_errors: list[str],
    src_root: Path,
    dst_root: Path,
) -> list[str]:
    """Validate OKF conformance and AIMS repository policy."""
    errors = list(parse_errors)
    sources = {document.source.resolve() for document in documents}
    for document in documents:
        errors.extend(validate_reserved_or_concept(document, src_root))
        errors.extend(validate_aims_policy(document, sources, src_root))
        expected = render_document(document, src_root, dst_root)
        if not document.destination.exists():
            errors.append(
                f"AIMS policy error: {document.destination}: generated file is missing"
            )
        elif document.destination.read_text(encoding="utf-8") != expected:
            errors.append(
                "AIMS policy error: "
                f"{document.destination}: generated file is out of date"
            )
    if not (src_root / "index.md").exists():
        errors.append(
            f"OKF conformance error: {src_root / 'index.md'}: bundle index is missing"
        )
    destination_set = {document.destination for document in documents}
    errors.extend(
        f"AIMS policy error: {generated}: stale generated file"
        for generated in (iter_markdown(dst_root) if dst_root.exists() else [])
        if generated not in destination_set
    )
    return errors


def validate_reserved_or_concept(document: OkfDocument, src_root: Path) -> list[str]:
    """Validate OKF v0.2 reserved-file and concept-document rules."""
    errors: list[str] = []
    if document.reserved:
        errors.extend(validate_reserved(document, src_root))
        return errors
    if not document.has_front_matter:
        errors.append(
            "OKF conformance error: "
            f"{document.source}: concept requires YAML front matter"
        )
    elif not _is_non_empty_string(document.metadata.get("type")):
        errors.append(
            "OKF conformance error: "
            f"{document.source}: concept requires non-empty 'type'"
        )
    else:
        errors.extend(validate_v02_metadata(document))
    return errors


def validate_reserved(document: OkfDocument, src_root: Path) -> list[str]:
    """Validate OKF v0.2 reserved Markdown files."""
    errors: list[str] = []
    if document.source.name == "log.md" and document.has_front_matter:
        errors.append(
            "OKF conformance error: "
            f"{document.source}: reserved log.md must not have concept front matter"
        )
    if document.source.name != "index.md" or not document.has_front_matter:
        return errors
    allowed_fields = (
        ROOT_INDEX_ALLOWED_FIELDS if document.source == src_root / "index.md" else set()
    )
    unknown = sorted(set(document.metadata) - allowed_fields)
    if unknown:
        errors.append(
            "OKF conformance error: "
            f"{document.source}: reserved index.md allows only "
            f"{sorted(allowed_fields)} front matter fields; found {unknown}"
        )
    if (
        document.source == src_root / "index.md"
        and document.metadata.get("okf_version") != "0.2"
    ):
        errors.append(
            f"AIMS policy error: {document.source}: okf_version must declare '0.2'"
        )
    return errors


def _is_non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_datetime(value: object) -> bool:
    if not isinstance(value, str) or "T" not in value:
        return False
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def _valid_date(value: object) -> bool:
    if not isinstance(value, str) or not ISO_DATE.fullmatch(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _metadata_error(document: OkfDocument, message: str) -> str:
    return f"AIMS policy error: {document.source}: {message}"


def _computation_sections(body: str) -> list[str]:
    """Text spans following each '# Computation' heading, up to the next H1.

    A line inside any open fence never starts or ends a section, so a
    fenced code example elsewhere in the body (e.g. one demonstrating
    ``# install deps`` or even a literal ``# Computation`` line) is never
    mistaken for a heading.
    """
    sections: list[list[str]] = []
    active = False
    marker = ""
    for line in body.splitlines():
        if marker:
            if active:
                sections[-1].append(line)
            fence = FENCE_LINE.match(line)
            if (
                fence
                and fence.group("marker")[0] == marker[0]
                and len(fence.group("marker")) >= len(marker)
            ):
                marker = ""
            continue
        if COMPUTATION_HEADING_LINE.match(line):
            sections.append([])
            active = True
            continue
        if HEADING_LINE.match(line):
            active = False
            continue
        if active:
            sections[-1].append(line)
        fence = FENCE_LINE.match(line)
        if fence:
            marker = fence.group("marker")
    return ["\n".join(section) for section in sections]


def _fenced_code_blocks(text: str) -> list[str]:
    """Non-empty fenced code blocks in ``text`` (``` or ~~~, indent <= 3)."""
    blocks: list[str] = []
    marker = ""
    code_lines: list[str] = []
    for line in text.splitlines():
        if marker:
            fence = FENCE_LINE.match(line)
            if (
                fence
                and fence.group("marker")[0] == marker[0]
                and len(fence.group("marker")) >= len(marker)
            ):
                if "".join(code_lines).strip():
                    blocks.append("".join(code_lines))
                marker = ""
                code_lines = []
            else:
                code_lines.append(line)
        else:
            fence = FENCE_LINE.match(line)
            if fence:
                marker = fence.group("marker")
    return blocks


def _computation_body_block_count(body: str) -> int:
    return sum(
        len(_fenced_code_blocks(section)) for section in _computation_sections(body)
    )


def _validate_actor_event(
    document: OkfDocument, field: str, event: object
) -> list[str]:
    if not isinstance(event, dict):
        return [_metadata_error(document, f"'{field}' must be a mapping")]
    errors: list[str] = []
    actor = event.get("by")
    if not _is_non_empty_string(actor) or not ACTOR.fullmatch(str(actor)):
        errors.append(
            _metadata_error(
                document,
                f"'{field}.by' must follow the OKF v0.2 actor convention",
            )
        )
    if not _valid_datetime(event.get("at")):
        errors.append(
            _metadata_error(document, f"'{field}.at' must be an ISO 8601 datetime")
        )
    return errors


def _validate_usage_window(
    document: OkfDocument, field: str, value: object
) -> list[str]:
    if not isinstance(value, dict):
        return [_metadata_error(document, f"'{field}' must be a mapping")]
    errors = [
        _metadata_error(
            document,
            f"'{field}.{boundary}' must be an ISO 8601 date",
        )
        for boundary in ("from", "to")
        if not _valid_date(value.get(boundary))
    ]
    if not errors and value["from"] > value["to"]:
        errors.append(
            _metadata_error(document, f"'{field}' must satisfy 'from' <= 'to'")
        )
    return errors


def _validate_sources(document: OkfDocument, value: object) -> list[str]:
    if not isinstance(value, list):
        return [_metadata_error(document, "'sources' must be a list")]
    if not value:
        return [_metadata_error(document, "'sources' must not be an empty list")]
    errors: list[str] = []
    for index, source in enumerate(value):
        field = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(_metadata_error(document, f"'{field}' must be a mapping"))
            continue
        if not _is_non_empty_string(source.get("resource")):
            errors.append(
                _metadata_error(
                    document, f"'{field}.resource' must be a non-empty string"
                )
            )
        errors.extend(
            _metadata_error(
                document,
                f"'{field}.{optional}' must be a non-empty string",
            )
            for optional in ("id", "title")
            if optional in source and not _is_non_empty_string(source[optional])
        )
        if "author" in source and (
            not _is_non_empty_string(source["author"])
            or not ACTOR.fullmatch(str(source["author"]))
        ):
            errors.append(
                _metadata_error(
                    document,
                    f"'{field}.author' must follow the OKF v0.2 actor convention",
                )
            )
        if "usage_count" in source:
            if (
                not isinstance(source["usage_count"], int)
                or isinstance(source["usage_count"], bool)
                or source["usage_count"] < 0
            ):
                errors.append(
                    _metadata_error(
                        document,
                        f"'{field}.usage_count' must be a non-negative integer",
                    )
                )
            if "usage_window" not in source and "usage_window" not in document.metadata:
                errors.append(
                    _metadata_error(
                        document,
                        f"'{field}.usage_count' requires '{field}.usage_window' "
                        "or a document-level 'usage_window'",
                    )
                )
        if "last_modified" in source and not _valid_date(source["last_modified"]):
            errors.append(
                _metadata_error(
                    document,
                    f"'{field}.last_modified' must be an ISO 8601 date",
                )
            )
        if "usage_window" in source:
            errors.extend(
                _validate_usage_window(
                    document, f"{field}.usage_window", source["usage_window"]
                )
            )
    return errors


def _validate_parameters(document: OkfDocument, value: object) -> list[str]:
    if not isinstance(value, list):
        return [_metadata_error(document, "'parameters' must be a list")]
    errors: list[str] = []
    for index, parameter in enumerate(value):
        field = f"parameters[{index}]"
        if not isinstance(parameter, dict):
            errors.append(_metadata_error(document, f"'{field}' must be a mapping"))
            continue
        errors.extend(
            _metadata_error(
                document,
                f"'{field}.{required_string}' must be a non-empty string",
            )
            for required_string in ("name", "type")
            if not _is_non_empty_string(parameter.get(required_string))
        )
        if not isinstance(parameter.get("required"), bool):
            errors.append(
                _metadata_error(document, f"'{field}.required' must be a boolean")
            )
    return errors


def _validate_resource_mapping(
    document: OkfDocument, field: str, value: object, *, receipt: bool
) -> list[str]:
    if not isinstance(value, dict):
        return [_metadata_error(document, f"'{field}' must be a mapping")]
    errors: list[str] = []
    if not _is_non_empty_string(value.get("resource")):
        errors.append(
            _metadata_error(document, f"'{field}.resource' must be a non-empty string")
        )
    if receipt and (
        not isinstance(value.get("receipt"), list)
        or not value["receipt"]
        or any(not _is_non_empty_string(item) for item in value["receipt"])
    ):
        errors.append(
            _metadata_error(
                document, f"'{field}.receipt' must be a non-empty string list"
            )
        )
    return errors


def validate_v02_metadata(document: OkfDocument) -> list[str]:
    """Validate standardized OKF v0.2 metadata used by AIMS."""
    metadata = document.metadata
    errors: list[str] = []
    if "timestamp" in metadata:
        errors.append(
            _metadata_error(
                document, "legacy 'timestamp' is superseded by 'generated.at'"
            )
        )
    if CITATIONS_HEADING.search(document.body):
        errors.append(
            _metadata_error(
                document, "body-level '# Citations' is superseded by 'sources'"
            )
        )
    if "resource" in metadata and not _is_non_empty_string(metadata["resource"]):
        errors.append(
            _metadata_error(document, "'resource' must be a non-empty URI or path")
        )
    if "status" in metadata and (
        not isinstance(metadata["status"], str)
        or metadata["status"] not in LIFECYCLE_STATUSES
    ):
        errors.append(
            _metadata_error(document, "'status' must be draft, stable, or deprecated")
        )
    if "generated" in metadata:
        errors.extend(
            _validate_actor_event(document, "generated", metadata["generated"])
        )
    if "verified" in metadata:
        verified = metadata["verified"]
        events = verified if isinstance(verified, list) else [verified]
        if not events:
            errors.append(
                _metadata_error(document, "'verified' must not be an empty list")
            )
        for index, event in enumerate(events):
            errors.extend(_validate_actor_event(document, f"verified[{index}]", event))
    if "stale_after" in metadata and not _valid_date(metadata["stale_after"]):
        errors.append(
            _metadata_error(document, "'stale_after' must be an ISO 8601 date")
        )
    if "sources" in metadata:
        errors.extend(_validate_sources(document, metadata["sources"]))
    if "usage_window" in metadata:
        errors.extend(
            _validate_usage_window(document, "usage_window", metadata["usage_window"])
        )
    if "computation" in metadata and not _is_non_empty_string(metadata["computation"]):
        errors.append(
            _metadata_error(document, "'computation' must be a non-empty URI or path")
        )
    if "parameters" in metadata:
        errors.extend(_validate_parameters(document, metadata["parameters"]))
    if "executor" in metadata:
        errors.extend(
            _validate_resource_mapping(
                document, "executor", metadata["executor"], receipt=True
            )
        )
    if "attester" in metadata:
        errors.extend(
            _validate_resource_mapping(
                document, "attester", metadata["attester"], receipt=False
            )
        )
    if metadata.get("type") == "Attested Computation":
        if not _is_non_empty_string(metadata.get("runtime")):
            errors.append(
                _metadata_error(
                    document,
                    "'runtime' is required for an Attested Computation",
                )
            )
        has_computation_file = _is_non_empty_string(metadata.get("computation"))
        computation_block_count = _computation_body_block_count(document.body)
        has_computation_body = computation_block_count > 0
        if has_computation_file and has_computation_body:
            errors.append(
                _metadata_error(
                    document,
                    "an Attested Computation must not set both a 'computation' "
                    "path and a body '# Computation' fenced code block",
                )
            )
        elif not has_computation_file and not has_computation_body:
            errors.append(
                _metadata_error(
                    document,
                    "an Attested Computation requires a 'computation' path or "
                    "a non-empty body '# Computation' fenced code block",
                )
            )
        elif not has_computation_file and computation_block_count > 1:
            errors.append(
                _metadata_error(
                    document,
                    "an Attested Computation body '# Computation' section must "
                    "contain exactly one fenced code block",
                )
            )
    return errors


def validate_aims_policy(
    document: OkfDocument, sources: set[Path], src_root: Path
) -> list[str]:
    """Validate AIMS metadata, tag, and link policies."""
    errors: list[str] = []
    if not document.reserved:
        errors.extend(
            "AIMS policy error: "
            f"{document.source}: recommended field '{field}' is missing"
            for field in RECOMMENDED_CONCEPT_FIELDS
            if field not in document.metadata
        )
        tags = document.metadata.get("tags")
        if not isinstance(tags, list) or not tags:
            errors.append(
                f"AIMS policy error: {document.source}: tags should be a non-empty list"
            )
        else:
            errors.extend(
                f"AIMS policy error: {document.source}: invalid tag '{tag}'"
                for tag in tags
                if not TAG.fullmatch(str(tag))
            )
    errors.extend(validate_links(document, sources, src_root))
    return errors


def pending_link(target: str) -> bool:
    """Return whether a link explicitly declares itself pending."""
    return "pending=true" in target or target.endswith("#pending")


def validate_links(
    document: OkfDocument, sources: set[Path], src_root: Path
) -> list[str]:
    """Validate resolvable relative and bundle-absolute Markdown links."""
    errors: list[str] = []
    for match in LINK.finditer(document.body):
        target = match.group("target")
        clean_target = target.split("?", 1)[0].split("#", 1)[0]
        if (
            not clean_target
            or "://" in clean_target
            or clean_target.startswith("mailto:")
            or pending_link(target)
        ):
            continue
        resolved = resolve_internal_okf_target(document, clean_target, src_root)
        if resolved is None:
            errors.append(
                "AIMS policy error: "
                f"{document.source}: unsafe internal link '{target}' "
                "escapes OKF bundle"
            )
            continue
        if resolved not in sources:
            errors.append(
                f"AIMS policy error: {document.source}: broken link '{target}'"
            )
    return errors


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=Path("okf"))
    parser.add_argument("--dst", type=Path, default=Path("content/knowledge"))
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--clean", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the OKF-to-Hugo adapter."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    documents, parse_errors = load_documents(args.src, args.dst)
    if args.check:
        errors = validate_documents(documents, parse_errors, args.src, args.dst)
        for error in errors:
            print(error, file=sys.stderr)
        return 1 if errors else 0
    if parse_errors:
        for error in parse_errors:
            print(error, file=sys.stderr)
        return 1
    write_documents(documents, args.src, args.dst, args.clean)
    return 0
