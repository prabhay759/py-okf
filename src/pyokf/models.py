"""Data models for py-okf."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ConceptType(Enum):
    """Supported OKF concept types for Python constructs."""
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    API = "api"


@dataclass
class OKFConcept:
    """Represents one OKF file (one markdown file with YAML frontmatter)."""
    type: ConceptType
    title: str
    description: str
    resource: str
    output_path: str
    tags: list[str] = field(default_factory=list)
    timestamp: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now(tz=datetime.timezone.utc)
    )
    content: str = ""
    extra_frontmatter: dict = field(default_factory=dict)


@dataclass
class ArgumentInfo:
    """Represents one parameter in a function/method signature."""
    name: str
    annotation: Optional[str] = None
    default: Optional[str] = None
    kind: str = "positional"


@dataclass
class AttributeInfo:
    """Represents a class-level annotated attribute."""
    name: str
    annotation: Optional[str] = None
    default: Optional[str] = None


@dataclass
class MethodInfo:
    """Represents one method inside a class."""
    name: str
    signature: str
    docstring: Optional[str] = None
    decorators: list[str] = field(default_factory=list)
    is_async: bool = False
    args: list[ArgumentInfo] = field(default_factory=list)
    returns: Optional[str] = None
    line_number: int = 0

    @property
    def is_public(self) -> bool:
        return not self.name.startswith("_")

    @property
    def is_dunder(self) -> bool:
        return self.name.startswith("__") and self.name.endswith("__")


@dataclass
class FunctionInfo:
    """Represents a top-level module function."""
    name: str
    module_name: str
    source_file: str
    signature: str
    docstring: Optional[str] = None
    decorators: list[str] = field(default_factory=list)
    is_async: bool = False
    args: list[ArgumentInfo] = field(default_factory=list)
    returns: Optional[str] = None
    is_exported: bool = False
    line_number: int = 0

    @property
    def is_public(self) -> bool:
        return not self.name.startswith("_")

    @property
    def concept_type(self) -> ConceptType:
        return ConceptType.API if self.is_exported else ConceptType.FUNCTION


@dataclass
class ClassInfo:
    """Represents a class definition extracted from AST."""
    name: str
    module_name: str
    source_file: str
    docstring: Optional[str] = None
    bases: list[str] = field(default_factory=list)
    attributes: list[AttributeInfo] = field(default_factory=list)
    methods: list[MethodInfo] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    line_number: int = 0

    @property
    def public_methods(self) -> list[MethodInfo]:
        return [m for m in self.methods if m.is_public]

    @property
    def dunder_methods(self) -> list[MethodInfo]:
        return [m for m in self.methods if m.is_dunder]


@dataclass
class ModuleInfo:
    """Represents a fully analyzed Python module file."""
    name: str
    source_file: str
    docstring: Optional[str] = None
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)

    @property
    def public_functions(self) -> list[FunctionInfo]:
        return [f for f in self.functions if f.is_public]
