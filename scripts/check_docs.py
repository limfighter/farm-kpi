"""Offline docs-as-code audit: local links, inventory and ADR structure."""
import argparse
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r'(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)')
ADR_TITLE = re.compile(r"^# ADR-[0-9]{4}:", re.MULTILINE)
TYPES = {"index", "tutorial", "how-to", "reference", "explanation", "decision", "template"}
OWNERS = {"maintainer", "research", "model", "operator"}
LIFECYCLE = {"active", "accepted", "historical", "template"}
REQUIRED = {"docs/README.md", "docs/STATUS.md", "docs/CONTRIBUTING_DOCS.md",
            "docs/decisions/README.md"}
SECTIONS = ("## 상황", "## 대안", "## 결정", "## 결과/검증")


def without_fences(text):
    active = False
    marker = ""
    visible = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(chr(96) * 3) or stripped.startswith("~~~"):
            prefix = stripped[:3]
            if not active:
                active, marker = True, prefix
            elif prefix == marker:
                active, marker = False, ""
            visible.append("")
        else:
            visible.append("" if active else line)
    return "\n".join(visible)


def link_path(target):
    target = target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    target = re.split(r'\s+"[^"]*"$', target, maxsplit=1)[0]
    if not target or target.startswith("#"):
        return None
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return None
    return unquote(parsed.path) or None


def audit(root=ROOT):
    root = Path(root).resolve()
    metadata = root / "docs/catalog.json"
    if not metadata.is_file():
        return ["Missing docs/catalog.json"]
    try:
        catalog = json.loads(metadata.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"Invalid docs catalog: {exc}"]
    errors = []
    if catalog.get("schema_version") != 1:
        errors.append("Invalid docs catalog schema_version")
    records = catalog.get("documents")
    if not isinstance(records, list):
        return errors + ["Catalog documents must be a list"]
    paths = []
    for i, rec in enumerate(records, 1):
        if not isinstance(rec, dict):
            errors.append(f"Catalog entry {i}: expected object")
            continue
        path = rec.get("path")
        if not isinstance(path, str) or not path.startswith("docs/") or not path.endswith(".md") or ".." in Path(path).parts:
            errors.append(f"Catalog entry {i}: invalid path")
            continue
        paths.append(path)
        if rec.get("type") not in TYPES:
            errors.append(f"Invalid type: {path}")
        if rec.get("owner") not in OWNERS:
            errors.append(f"Invalid owner: {path}")
        if rec.get("lifecycle") not in LIFECYCLE:
            errors.append(f"Invalid lifecycle: {path}")
        if rec.get("type") == "decision" and rec.get("lifecycle") != "accepted":
            errors.append(f"Decision not accepted: {path}")
        if rec.get("type") == "template" and rec.get("lifecycle") != "template":
            errors.append(f"Template lifecycle mismatch: {path}")
    if len(set(paths)) != len(paths):
        errors.append("Duplicate catalog paths")
    if not REQUIRED.issubset(paths):
        errors.append("Missing catalog entry for required hub/status/policy/ADR index")
    for key in ("current_status", "entrypoint", "policy", "documentation_sources"):
        if catalog.get(key) not in paths:
            errors.append(f"Unregistered authoritative document: {key}")

    found = {p.relative_to(root).as_posix() for p in (root / "docs").rglob("*.md")}
    for path in sorted(found - set(paths)):
        errors.append(f"Missing catalog entry: {path}")
    for path in sorted(set(paths) - found):
        errors.append(f"Nonexistent catalog document: {path}")

    for source in [root / "README.md"] + sorted((root / "docs").rglob("*.md")):
        rel = source.relative_to(root).as_posix()
        if not source.is_file():
            errors.append(f"Missing Markdown: {rel}")
            continue
        content = source.read_text(encoding="utf-8")
        if not content.startswith("# "):
            errors.append(f"Top-level title missing: {rel}")
        for text in LINK.findall(without_fences(content)):
            dest = link_path(text)
            if dest is None:
                continue
            if dest.startswith("/"):
                errors.append(f"Absolute repo link: {rel}: {text}")
                continue
            resolved = (source.parent / dest).resolve()
            if resolved != root and root not in resolved.parents:
                errors.append(f"Path escape: {rel}: {text}")
            elif not resolved.exists():
                errors.append(f"Broken local link: {rel}: {text}")

    for rec in records:
        if not isinstance(rec, dict) or rec.get("type") != "decision":
            continue
        path = rec.get("path")
        if path not in found:
            continue
        body = (root / path).read_text(encoding="utf-8")
        if not ADR_TITLE.search(body):
            errors.append(f"ADR title missing: {path}")
        if not re.search(r"\*\*상태:\*\*\s+Accepted\b", body):
            errors.append(f"ADR status missing: {path}")
        if not re.search(r"\*\*날짜:\*\*\s+\d{4}-\d{2}-\d{2}", body):
            errors.append(f"ADR date missing: {path}")
        for section in SECTIONS:
            if section not in body:
                errors.append(f"ADR section missing: {path}: {section}")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Check docs inventory and local Markdown links")
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    issues = audit()
    if issues:
        for issue in issues:
            print("DOCS ERROR: " + issue)
        return 1
    print("Docs audit passed: catalog, relative links, ADR fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
