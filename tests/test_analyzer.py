"""Tests for pyokf.analyzer."""

from pathlib import Path

import pytest

from pyokf.analyzer import analyze_file, analyze_project
from pyokf.models import ConceptType


def test_analyze_file_returns_module_info(sample_py_file):
    module = analyze_file(sample_py_file)
    assert module.name == "sample"
    assert "sample module" in module.docstring.lower()


def test_analyze_file_extracts_class(sample_py_file):
    module = analyze_file(sample_py_file)
    assert len(module.classes) == 1
    cls = module.classes[0]
    assert cls.name == "Connection"
    assert "database" in cls.docstring.lower()


def test_analyze_file_class_attributes(sample_py_file):
    module = analyze_file(sample_py_file)
    cls = module.classes[0]
    attr_names = [a.name for a in cls.attributes]
    assert "host" in attr_names
    assert "port" in attr_names


def test_analyze_file_class_methods(sample_py_file):
    module = analyze_file(sample_py_file)
    cls = module.classes[0]
    method_names = [m.name for m in cls.methods]
    assert "__init__" in method_names
    assert "connect" in method_names
    assert "from_url" in method_names
    assert "_internal" in method_names


def test_analyze_file_init_args(sample_py_file):
    module = analyze_file(sample_py_file)
    cls = module.classes[0]
    init = next(m for m in cls.methods if m.name == "__init__")
    arg_names = [a.name for a in init.args]
    assert "self" in arg_names
    assert "host" in arg_names
    assert "port" in arg_names

    port_arg = next(a for a in init.args if a.name == "port")
    assert port_arg.annotation == "int"
    assert port_arg.default == "5432"


def test_analyze_file_classmethod_decorator(sample_py_file):
    module = analyze_file(sample_py_file)
    cls = module.classes[0]
    from_url = next(m for m in cls.methods if m.name == "from_url")
    assert "classmethod" in from_url.decorators


def test_analyze_file_exports(sample_py_file):
    module = analyze_file(sample_py_file)
    assert module.exports == ["query"]


def test_analyze_file_function_is_exported(sample_py_file):
    module = analyze_file(sample_py_file)
    query_fn = next(f for f in module.functions if f.name == "query")
    assert query_fn.is_exported is True
    assert query_fn.concept_type == ConceptType.API


def test_analyze_file_private_function_not_exported(sample_py_file):
    module = analyze_file(sample_py_file)
    helper = next(f for f in module.functions if f.name == "_helper")
    assert helper.is_exported is False
    assert helper.is_public is False


def test_analyze_project_finds_modules(sample_project):
    modules = analyze_project(sample_project)
    names = [m.name for m in modules]
    assert "mypackage" in names
    assert "mypackage.utils" in names


def test_analyze_project_excludes_private_files(tmp_path):
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "_internal.py").write_text("def secret(): pass\n")
    (pkg / "public.py").write_text("def visible(): pass\n")

    modules = analyze_project(tmp_path, include_private=False)
    names = [m.name for m in modules]
    assert "mypkg.public" in names
    assert "mypkg._internal" not in names


def test_analyze_project_includes_private_files_when_flag_set(tmp_path):
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "_internal.py").write_text("def secret(): pass\n")

    modules = analyze_project(tmp_path, include_private=True)
    names = [m.name for m in modules]
    assert "mypkg._internal" in names


def test_analyze_project_skips_syntax_errors(tmp_path):
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "broken.py").write_text("def bad syntax(:\n")
    (pkg / "good.py").write_text("def ok(): pass\n")

    modules = analyze_project(tmp_path)
    names = [m.name for m in modules]
    assert "mypkg.good" in names
    assert "mypkg.broken" not in names


def test_analyze_file_with_src_layout(tmp_path):
    src = tmp_path / "src"
    pkg = src / "mypkg"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text('"""My pkg."""\n')
    (pkg / "utils.py").write_text('"""Utils."""\ndef do(): pass\n')

    modules = analyze_project(tmp_path)
    names = [m.name for m in modules]
    assert "mypkg" in names
    assert "mypkg.utils" in names
