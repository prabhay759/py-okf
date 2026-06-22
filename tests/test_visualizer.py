"""Tests for pyokf.visualizer."""

import json
from pathlib import Path

import pytest

from pyokf.analyzer import analyze_file
from pyokf.cli import main
from pyokf.generator import generate_module_concepts
from pyokf.visualizer import generate_html


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _all_concepts(sample_py_file):
    module = analyze_file(sample_py_file)
    return generate_module_concepts(module)


def run_cli(*args):
    with pytest.raises(SystemExit) as exc:
        main(list(args))
    return exc.value.code


# ---------------------------------------------------------------------------
# generate_html unit tests
# ---------------------------------------------------------------------------

def test_generate_html_returns_string(sample_py_file):
    concepts = _all_concepts(sample_py_file)
    result = generate_html(concepts)
    assert isinstance(result, str)
    assert len(result) > 0


def test_html_has_doctype(sample_py_file):
    concepts = _all_concepts(sample_py_file)
    html = generate_html(concepts)
    assert html.startswith("<!DOCTYPE html>")


def test_html_has_html_open_close(sample_py_file):
    concepts = _all_concepts(sample_py_file)
    html = generate_html(concepts)
    assert "<html" in html
    assert "</html>" in html


def test_html_embeds_concept_titles(sample_py_file):
    concepts = _all_concepts(sample_py_file)
    html = generate_html(concepts)
    for c in concepts:
        assert c.title in html


def test_html_no_external_urls(sample_py_file):
    concepts = _all_concepts(sample_py_file)
    html = generate_html(concepts)
    # Strip out the concept content (resource paths like ./sample.py are fine)
    # Focus on script/link/img src tags pointing to external hosts
    import re
    # Look for http:// or https:// in src/href attributes of script, link, img tags
    external = re.findall(r'(?:src|href)=["\']https?://', html)
    assert external == [], f"Found external URLs: {external}"


def test_html_empty_concepts():
    html = generate_html([])
    assert "<!DOCTYPE html>" in html
    assert "0 concept" in html


def test_html_single_concept(sample_py_file):
    concepts = _all_concepts(sample_py_file)
    html = generate_html(concepts[:1])
    assert "1 concept" in html
    # No trailing 's'
    assert "1 concepts" not in html


def test_html_plural_concepts(sample_py_file):
    concepts = _all_concepts(sample_py_file)
    assert len(concepts) > 1
    html = generate_html(concepts)
    assert f"{len(concepts)} concepts" in html


def test_html_escapes_special_chars():
    from pyokf.models import ConceptType, OKFConcept
    import datetime

    concept = OKFConcept(
        type=ConceptType.MODULE,
        title='<script>alert("xss")</script>',
        description="A & B < C > D",
        resource="./f.py",
        output_path="f.md",
        content="",
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
    )
    html = generate_html([concept])
    # The raw script tag should NOT appear unescaped in the HTML output
    # (it will be JSON-encoded in the DATA variable)
    assert '<script>alert("xss")</script>' not in html
    # But the JSON-encoded version should be present (escaped)
    assert "alert" in html  # content is in the JSON blob


def test_html_contains_type_colors(sample_py_file):
    concepts = _all_concepts(sample_py_file)
    html = generate_html(concepts)
    # Type color values embedded in CSS/JS
    assert "#3b82f6" in html  # module
    assert "#10b981" in html  # class


def test_html_concepts_sorted_alphabetically(sample_py_file):
    concepts = _all_concepts(sample_py_file)
    html = generate_html(concepts)
    # Parse the embedded JSON from the DATA= assignment
    import re
    m = re.search(r'const DATA=(\[.*?\]);', html, re.DOTALL)
    assert m, "Could not find DATA= in HTML"
    data = json.loads(m.group(1).replace("\\/", "/"))
    titles = [d["title"] for d in data]
    assert titles == sorted(titles), "Concepts should be sorted alphabetically by title"


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def test_cli_view_creates_index_html(sample_project):
    run_cli("generate", str(sample_project))
    code = run_cli("view", str(sample_project))
    assert code == 0
    index = sample_project / ".okf" / "index.html"
    assert index.exists()
    content = index.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content


def test_cli_view_html_is_valid(sample_project):
    run_cli("generate", str(sample_project))
    run_cli("view", str(sample_project))
    html = (sample_project / ".okf" / "index.html").read_text(encoding="utf-8")
    assert "<style>" in html
    assert "<script>" in html
    assert "const DATA=" in html


def test_cli_view_exits_1_without_bundle(tmp_path):
    code = run_cli("view", str(tmp_path))
    assert code == 1


def test_cli_view_exits_1_with_empty_okf_dir(tmp_path):
    okf_dir = tmp_path / ".okf"
    okf_dir.mkdir()
    code = run_cli("view", str(tmp_path))
    assert code == 1


def test_cli_view_custom_output_dir(sample_project, tmp_path):
    custom = tmp_path / "myokf"
    run_cli("generate", str(sample_project), "-o", str(custom))
    code = run_cli("view", str(sample_project), "-o", str(custom))
    assert code == 0
    assert (custom / "index.html").exists()
