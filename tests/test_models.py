"""Tests for pyokf.models."""

import datetime

import pytest

from pyokf.models import (
    ArgumentInfo,
    ClassInfo,
    ConceptType,
    FunctionInfo,
    MethodInfo,
    ModuleInfo,
    OKFConcept,
)


def test_concept_type_values():
    assert ConceptType.MODULE.value == "module"
    assert ConceptType.CLASS.value == "class"
    assert ConceptType.FUNCTION.value == "function"
    assert ConceptType.API.value == "api"


def test_okf_concept_default_timestamp_is_utc():
    concept = OKFConcept(
        type=ConceptType.MODULE,
        title="test",
        description="desc",
        resource="./test.py",
        output_path="test.md",
    )
    assert concept.timestamp.tzinfo is not None
    assert concept.timestamp.tzinfo == datetime.timezone.utc


def test_method_info_is_public():
    assert MethodInfo(name="connect", signature="def connect(self)").is_public is True
    assert MethodInfo(name="_internal", signature="def _internal(self)").is_public is False


def test_method_info_is_dunder():
    assert MethodInfo(name="__init__", signature="def __init__(self)").is_dunder is True
    assert MethodInfo(name="connect", signature="def connect(self)").is_dunder is False
    assert MethodInfo(name="_internal", signature="def _internal(self)").is_dunder is False


def test_class_info_public_methods():
    methods = [
        MethodInfo(name="connect", signature="def connect(self)"),
        MethodInfo(name="_internal", signature="def _internal(self)"),
        MethodInfo(name="__init__", signature="def __init__(self)"),
    ]
    cls = ClassInfo(name="Conn", module_name="mod", source_file="mod.py", methods=methods)
    public = cls.public_methods
    assert len(public) == 1
    assert public[0].name == "connect"


def test_class_info_dunder_methods():
    methods = [
        MethodInfo(name="connect", signature="def connect(self)"),
        MethodInfo(name="__init__", signature="def __init__(self)"),
        MethodInfo(name="__repr__", signature="def __repr__(self)"),
    ]
    cls = ClassInfo(name="Conn", module_name="mod", source_file="mod.py", methods=methods)
    dunders = cls.dunder_methods
    assert {m.name for m in dunders} == {"__init__", "__repr__"}


def test_function_info_concept_type_api_when_exported():
    fn = FunctionInfo(
        name="query",
        module_name="mod",
        source_file="mod.py",
        signature="def query(sql)",
        is_exported=True,
    )
    assert fn.concept_type == ConceptType.API


def test_function_info_concept_type_function_when_not_exported():
    fn = FunctionInfo(
        name="helper",
        module_name="mod",
        source_file="mod.py",
        signature="def helper(x)",
        is_exported=False,
    )
    assert fn.concept_type == ConceptType.FUNCTION


def test_function_info_is_public():
    pub = FunctionInfo(name="query", module_name="m", source_file="m.py", signature="def query()")
    priv = FunctionInfo(name="_helper", module_name="m", source_file="m.py", signature="def _helper()")
    assert pub.is_public is True
    assert priv.is_public is False


def test_module_info_public_functions():
    fns = [
        FunctionInfo(name="query", module_name="m", source_file="m.py", signature="def query()"),
        FunctionInfo(name="_helper", module_name="m", source_file="m.py", signature="def _helper()"),
    ]
    module = ModuleInfo(name="m", source_file="m.py", functions=fns)
    assert len(module.public_functions) == 1
    assert module.public_functions[0].name == "query"
