"""Tests for pyokf.bundle."""

import datetime
import time
from pathlib import Path

import pytest

from pyokf.analyzer import analyze_file
from pyokf.bundle import OKFBundle, VALID_TYPES
from pyokf.generator import generate_module_concept, generate_concept
from pyokf.models import ConceptType, OKFConcept

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_load_bundle_from_fixture():
    bundle = OKFBundle(FIXTURES_DIR / "sample_okf").load()
    assert len(bundle.concepts) == 1
    concept = bundle.concepts[0]
    assert concept.type == ConceptType.MODULE
    assert concept.title == "sample"


def test_load_bundle_empty_dir(tmp_path):
    bundle = OKFBundle(tmp_path / "nonexistent").load()
    assert bundle.concepts == []


def test_write_and_reload(tmp_path, sample_py_file):
    module = analyze_file(sample_py_file)
    concept = generate_module_concept(module)

    bundle = OKFBundle(tmp_path / ".okf")
    bundle.ensure_directory()
    path = bundle.write(concept)

    assert path.exists()
    content = path.read_text()
    assert content.startswith("---\n")
    assert "type: module" in content

    reloaded = OKFBundle(tmp_path / ".okf").load()
    assert len(reloaded.concepts) == 1
    assert reloaded.concepts[0].title == concept.title


def test_write_no_overwrite(tmp_path, sample_py_file):
    module = analyze_file(sample_py_file)
    concept = generate_module_concept(module)

    bundle = OKFBundle(tmp_path / ".okf")
    bundle.ensure_directory()
    bundle.write(concept)

    out_path = bundle.directory / concept.output_path
    original_mtime = out_path.stat().st_mtime

    time.sleep(0.01)
    bundle.write(concept, overwrite=False)
    assert out_path.stat().st_mtime == original_mtime


def test_write_all(tmp_path, sample_py_file):
    from pyokf.generator import generate_module_concepts
    module = analyze_file(sample_py_file)
    concepts = generate_module_concepts(module)

    bundle = OKFBundle(tmp_path / ".okf")
    bundle.ensure_directory()
    paths = bundle.write_all(concepts)

    assert len(paths) == len(concepts)
    for p in paths:
        assert p.exists()


def test_needs_refresh_when_no_existing_concept(tmp_path, sample_py_file):
    module = analyze_file(sample_py_file)
    concept = generate_module_concept(module)

    bundle = OKFBundle(tmp_path / ".okf")
    mtime = sample_py_file.stat().st_mtime
    assert bundle.needs_refresh(concept, mtime) is True


def test_needs_refresh_when_source_is_newer(tmp_path, sample_py_file):
    module = analyze_file(sample_py_file)
    concept = generate_module_concept(module)

    bundle = OKFBundle(tmp_path / ".okf")
    bundle.ensure_directory()
    bundle.write(concept)

    # Simulate source file being modified after OKF was generated
    future_mtime = datetime.datetime.now(tz=datetime.timezone.utc).timestamp() + 3600
    assert bundle.needs_refresh(concept, future_mtime) is True


def test_needs_refresh_false_when_up_to_date(tmp_path, sample_py_file):
    module = analyze_file(sample_py_file)
    concept = generate_module_concept(module)

    bundle = OKFBundle(tmp_path / ".okf")
    bundle.ensure_directory()
    bundle.write(concept)

    # Source file mtime is in the past relative to the generated OKF
    past_mtime = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc).timestamp()
    assert bundle.needs_refresh(concept, past_mtime) is False


def test_validate_file_valid(tmp_path):
    md = tmp_path / "valid.md"
    md.write_text(
        "---\ntype: module\ntitle: T\ndescription: D\nresource: ./f.py\ntimestamp: '2026-01-01T00:00:00Z'\n---\n\n# T\n",
        encoding="utf-8",
    )
    bundle = OKFBundle(tmp_path)
    errors = bundle.validate_file(md)
    assert errors == []


def test_validate_file_missing_type(tmp_path):
    md = tmp_path / "bad.md"
    md.write_text(
        "---\ntitle: T\ndescription: D\nresource: ./f.py\ntimestamp: '2026-01-01T00:00:00Z'\n---\n\n# T\n",
        encoding="utf-8",
    )
    bundle = OKFBundle(tmp_path)
    errors = bundle.validate_file(md)
    assert any("type" in e for e in errors)


def test_validate_file_invalid_type(tmp_path):
    md = tmp_path / "bad.md"
    md.write_text(
        "---\ntype: invalid_xyz\ntitle: T\ndescription: D\nresource: ./f.py\ntimestamp: '2026-01-01T00:00:00Z'\n---\n\n# T\n",
        encoding="utf-8",
    )
    bundle = OKFBundle(tmp_path)
    errors = bundle.validate_file(md)
    assert any("Invalid type" in e for e in errors)


def test_validate_file_missing_frontmatter(tmp_path):
    md = tmp_path / "bad.md"
    md.write_text("# Just a heading\n", encoding="utf-8")
    bundle = OKFBundle(tmp_path)
    errors = bundle.validate_file(md)
    assert any("frontmatter" in e.lower() for e in errors)


def test_validate_directory_all_valid(tmp_path):
    md = tmp_path / "ok.md"
    md.write_text(
        "---\ntype: api\ntitle: T\ndescription: D\nresource: ./f.py\ntimestamp: '2026-01-01T00:00:00Z'\n---\n\n# T\n",
        encoding="utf-8",
    )
    bundle = OKFBundle(tmp_path)
    results = bundle.validate_directory()
    assert results == {}


def test_validate_directory_reports_errors(tmp_path):
    md = tmp_path / "bad.md"
    md.write_text("# No frontmatter\n", encoding="utf-8")
    bundle = OKFBundle(tmp_path)
    results = bundle.validate_directory()
    assert str(md) in results


def test_valid_types_includes_vendor_types():
    assert "dataset" in VALID_TYPES
    assert "metric" in VALID_TYPES
    assert "playbook" in VALID_TYPES
    assert "runbook" in VALID_TYPES
    assert "table" in VALID_TYPES


def test_load_unknown_type_does_not_crash(tmp_path):
    md = tmp_path / "vendor.md"
    md.write_text(
        "---\ntype: dataset\ntitle: T\ndescription: D\nresource: ./f.py\ntimestamp: '2026-01-01T00:00:00Z'\n---\n\n# T\n",
        encoding="utf-8",
    )
    bundle = OKFBundle(tmp_path).load()
    assert len(bundle.concepts) == 1
