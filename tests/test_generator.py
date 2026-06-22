"""Tests for pyokf.generator."""

import yaml

from pyokf.analyzer import analyze_file
from pyokf.generator import (
    generate_class_concept,
    generate_concept,
    generate_function_concept,
    generate_module_concept,
    generate_module_concepts,
)
from pyokf.models import ConceptType


def test_generate_module_concept_type(sample_py_file):
    module = analyze_file(sample_py_file)
    concept = generate_module_concept(module)
    assert concept.type == ConceptType.MODULE


def test_generate_module_concept_title(sample_py_file):
    module = analyze_file(sample_py_file)
    concept = generate_module_concept(module)
    assert concept.title == "sample"


def test_generate_module_concept_content_has_classes_section(sample_py_file):
    module = analyze_file(sample_py_file)
    concept = generate_module_concept(module)
    assert "## Classes" in concept.content
    assert "Connection" in concept.content


def test_generate_module_concept_content_has_functions_section(sample_py_file):
    module = analyze_file(sample_py_file)
    concept = generate_module_concept(module)
    assert "## Functions" in concept.content
    assert "query" in concept.content


def test_generate_class_concept_type(sample_py_file):
    module = analyze_file(sample_py_file)
    cls = module.classes[0]
    concept = generate_class_concept(cls)
    assert concept.type == ConceptType.CLASS


def test_generate_class_concept_has_attributes_section(sample_py_file):
    module = analyze_file(sample_py_file)
    cls = module.classes[0]
    concept = generate_class_concept(cls)
    assert "## Attributes" in concept.content
    assert "host" in concept.content
    assert "port" in concept.content


def test_generate_class_concept_has_constructor_section(sample_py_file):
    module = analyze_file(sample_py_file)
    cls = module.classes[0]
    concept = generate_class_concept(cls)
    assert "## Constructor" in concept.content


def test_generate_class_concept_public_methods_only(sample_py_file):
    module = analyze_file(sample_py_file)
    cls = module.classes[0]
    concept = generate_class_concept(cls)
    assert "## Methods" in concept.content
    assert "connect" in concept.content
    assert "_internal" not in concept.content


def test_generate_function_concept_exported_is_api(sample_py_file):
    module = analyze_file(sample_py_file)
    query_fn = next(f for f in module.functions if f.name == "query")
    concept = generate_function_concept(query_fn)
    assert concept.type == ConceptType.API


def test_generate_function_concept_not_exported_is_function(sample_py_file):
    module = analyze_file(sample_py_file)
    helper = next(f for f in module.functions if f.name == "_helper")
    concept = generate_function_concept(helper)
    assert concept.type == ConceptType.FUNCTION


def test_generate_function_concept_has_signature_section(sample_py_file):
    module = analyze_file(sample_py_file)
    query_fn = next(f for f in module.functions if f.name == "query")
    concept = generate_function_concept(query_fn)
    assert "## Signature" in concept.content
    assert "```python" in concept.content


def test_generate_function_concept_has_parameters_section(sample_py_file):
    module = analyze_file(sample_py_file)
    query_fn = next(f for f in module.functions if f.name == "query")
    concept = generate_function_concept(query_fn)
    assert "## Parameters" in concept.content
    assert "sql" in concept.content


def test_generate_concept_produces_valid_frontmatter(sample_py_file):
    module = analyze_file(sample_py_file)
    concept = generate_module_concept(module)
    rendered = generate_concept(concept)

    assert rendered.startswith("---\n")
    parts = rendered.split("---", 2)
    fm = yaml.safe_load(parts[1])
    assert fm["type"] == "module"
    assert fm["title"] == "sample"
    assert "timestamp" in fm
    assert fm["timestamp"].endswith("Z")


def test_generate_concept_frontmatter_key_order(sample_py_file):
    module = analyze_file(sample_py_file)
    concept = generate_module_concept(module)
    rendered = generate_concept(concept)

    parts = rendered.split("---", 2)
    fm_text = parts[1]
    keys = [line.split(":")[0].strip() for line in fm_text.strip().splitlines() if ":" in line and not line.startswith(" ")]
    expected_order = ["type", "title", "description", "resource", "tags", "timestamp"]
    assert keys == expected_order


def test_generate_module_concepts_count(sample_py_file):
    module = analyze_file(sample_py_file)
    concepts = generate_module_concepts(module)
    # 1 module + 1 class + public functions (query)
    assert len(concepts) >= 3


def test_generate_module_concepts_excludes_private_by_default(sample_py_file):
    module = analyze_file(sample_py_file)
    concepts = generate_module_concepts(module)
    titles = [c.title for c in concepts]
    assert not any("_helper" in t for t in titles)


def test_generate_module_concepts_includes_private_with_flag(sample_py_file):
    module = analyze_file(sample_py_file)
    concepts = generate_module_concepts(module, include_private=True)
    titles = [c.title for c in concepts]
    assert any("_helper" in t for t in titles)
