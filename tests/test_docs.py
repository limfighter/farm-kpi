"""Docs-as-code checks: catalog, links and accepted decisions."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_docs.py"
spec = importlib.util.spec_from_file_location("check_docs", SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def test_live_documentation_inventory_and_internal_links():
    assert checker.audit(ROOT) == []


def test_local_link_url_parser_ignores_public_urls_and_fragments():
    assert checker.link_path("https://docs.gitlab.com/docs#section") is None
    assert checker.link_path("#local-anchor") is None
    assert checker.link_path("mailto:docs@example.com") is None
    assert checker.link_path("../data/report.csv#table") == "../data/report.csv"
    assert checker.link_path("reference/DATA_CONTRACTS.md") == "reference/DATA_CONTRACTS.md"


def test_markdown_fences_do_not_create_spurious_broken_links():
    raw = "# Heading\n" + chr(96)*3 + "md\n" + "[example](DOES-NOT-EXIST.md)\n" + chr(96)*3 + "\n[real](README.md)"
    without = checker.without_fences(raw)
    assert "DOES-NOT-EXIST.md" not in without
    assert "README.md" in without


def test_missing_catalog_entry_is_detected(tmp_path):
    d = tmp_path / "docs"
    d.mkdir()
    (tmp_path / "README.md").write_text("# Hello\n", encoding="utf-8")
    (d / "README.md").write_text("# Doc hub\n", encoding="utf-8")
    (d / "unregistered.md").write_text("# Missing from catalog\n", encoding="utf-8")
    manifest = {
        "schema_version": 1, "current_status": "docs/README.md",
        "entrypoint": "docs/README.md", "policy": "docs/README.md",
        "documentation_sources": "docs/README.md",
        "documents": [{"path": "docs/README.md", "type": "index",
                       "owner": "maintainer", "lifecycle": "active"}]
    }
    (d / "catalog.json").write_text(json.dumps(manifest), encoding="utf-8")
    errors = checker.audit(tmp_path)
    assert any("Missing catalog entry: docs/unregistered.md" in e for e in errors)


def test_broken_local_link_is_detected(tmp_path):
    d = tmp_path / "docs"
    d.mkdir()
    (tmp_path / "README.md").write_text("# Home\n[broken](docs/no.md)\n", encoding="utf-8")
    (d / "README.md").write_text("# Docs\n", encoding="utf-8")
    manifest = {
        "schema_version": 1, "current_status": "docs/README.md",
        "entrypoint": "docs/README.md", "policy": "docs/README.md",
        "documentation_sources": "docs/README.md",
        "documents": [{"path": "docs/README.md", "type": "index",
                       "owner": "maintainer", "lifecycle": "active"}]
    }
    (d / "catalog.json").write_text(json.dumps(manifest), encoding="utf-8")
    errors = checker.audit(tmp_path)
    assert any("Broken local link: README.md: docs/no.md" in e for e in errors)
