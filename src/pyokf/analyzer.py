"""Python AST analyzer for py-okf."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Optional

from pyokf.models import (
    ArgumentInfo,
    AttributeInfo,
    ClassInfo,
    FunctionInfo,
    MethodInfo,
    ModuleInfo,
)

_EXCLUDE_DIRS = frozenset({
    ".git", "__pycache__", ".tox", "build", "dist", ".eggs",
    "venv", ".venv", "env", ".env", "node_modules",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".okf",
})


def _extract_args(args: ast.arguments) -> list[ArgumentInfo]:
    result: list[ArgumentInfo] = []

    n_args = len(args.posonlyargs) + len(args.args)
    n_defaults = len(args.defaults)
    default_offset = n_args - n_defaults

    all_positional = args.posonlyargs + args.args
    for i, arg in enumerate(all_positional):
        default_idx = i - default_offset
        default = ast.unparse(args.defaults[default_idx]) if default_idx >= 0 else None
        annotation = ast.unparse(arg.annotation) if arg.annotation else None
        kind = "positional_only" if i < len(args.posonlyargs) else "positional"
        result.append(ArgumentInfo(name=arg.arg, annotation=annotation, default=default, kind=kind))

    if args.vararg:
        ann = ast.unparse(args.vararg.annotation) if args.vararg.annotation else None
        result.append(ArgumentInfo(name=args.vararg.arg, annotation=ann, kind="var_positional"))

    for i, arg in enumerate(args.kwonlyargs):
        kw_default = args.kw_defaults[i]
        default = ast.unparse(kw_default) if kw_default is not None else None
        ann = ast.unparse(arg.annotation) if arg.annotation else None
        result.append(ArgumentInfo(name=arg.arg, annotation=ann, default=default, kind="keyword_only"))

    if args.kwarg:
        ann = ast.unparse(args.kwarg.annotation) if args.kwarg.annotation else None
        result.append(ArgumentInfo(name=args.kwarg.arg, annotation=ann, kind="var_keyword"))

    return result


def _build_signature(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    unparsed = ast.unparse(func_node)
    first_line = unparsed.split("\n")[0]
    return first_line.rstrip(":")


def _extract_method(node: ast.FunctionDef | ast.AsyncFunctionDef) -> MethodInfo:
    return MethodInfo(
        name=node.name,
        signature=_build_signature(node),
        docstring=ast.get_docstring(node),
        decorators=[ast.unparse(d) for d in node.decorator_list],
        is_async=isinstance(node, ast.AsyncFunctionDef),
        args=_extract_args(node.args),
        returns=ast.unparse(node.returns) if node.returns else None,
        line_number=node.lineno,
    )


def _extract_class(node: ast.ClassDef, module_name: str, source_file: str) -> ClassInfo:
    attributes: list[AttributeInfo] = []
    methods: list[MethodInfo] = []

    for item in node.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            attributes.append(AttributeInfo(
                name=item.target.id,
                annotation=ast.unparse(item.annotation) if item.annotation else None,
                default=ast.unparse(item.value) if item.value else None,
            ))
        elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(_extract_method(item))

    return ClassInfo(
        name=node.name,
        module_name=module_name,
        source_file=source_file,
        docstring=ast.get_docstring(node),
        bases=[ast.unparse(b) for b in node.bases],
        attributes=attributes,
        methods=methods,
        decorators=[ast.unparse(d) for d in node.decorator_list],
        line_number=node.lineno,
    )


def _extract_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    module_name: str,
    source_file: str,
    exports: list[str],
) -> FunctionInfo:
    return FunctionInfo(
        name=node.name,
        module_name=module_name,
        source_file=source_file,
        signature=_build_signature(node),
        docstring=ast.get_docstring(node),
        decorators=[ast.unparse(d) for d in node.decorator_list],
        is_async=isinstance(node, ast.AsyncFunctionDef),
        args=_extract_args(node.args),
        returns=ast.unparse(node.returns) if node.returns else None,
        is_exported=node.name in exports,
        line_number=node.lineno,
    )


def _extract_exports(tree: ast.Module) -> list[str]:
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "__all__"
            and isinstance(node.value, (ast.List, ast.Tuple))
        ):
            return [
                elt.s for elt in node.value.elts
                if isinstance(elt, ast.Constant) and isinstance(elt.s, str)
            ]
    return []


def _path_to_module_name(py_file: Path, package_root: Path) -> str:
    rel = py_file.relative_to(package_root)
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) if parts else package_root.name


def analyze_file(
    py_file: Path,
    module_name: Optional[str] = None,
    package_root: Optional[Path] = None,
) -> ModuleInfo:
    """Analyze a single Python file and return a ModuleInfo."""
    py_file = Path(py_file).resolve()
    if package_root is None:
        package_root = py_file.parent
    else:
        package_root = Path(package_root).resolve()

    source = py_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(py_file))

    if module_name is None:
        module_name = _path_to_module_name(py_file, package_root)

    source_file = str(py_file.relative_to(package_root))
    exports = _extract_exports(tree)
    classes: list[ClassInfo] = []
    functions: list[FunctionInfo] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(_extract_class(node, module_name, source_file))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(_extract_function(node, module_name, source_file, exports))

    return ModuleInfo(
        name=module_name,
        source_file=source_file,
        docstring=ast.get_docstring(tree),
        classes=classes,
        functions=functions,
        exports=exports,
    )


def analyze_project(
    project_root: Path,
    include_private: bool = False,
) -> list[ModuleInfo]:
    """Walk a Python project and analyze all .py files."""
    project_root = Path(project_root).resolve()

    src_dir = project_root / "src"
    has_src_layout = src_dir.is_dir()

    modules: list[ModuleInfo] = []
    for py_file in sorted(project_root.rglob("*.py")):
        if any(part in _EXCLUDE_DIRS for part in py_file.parts):
            continue
        if not include_private and py_file.name.startswith("_") and py_file.name != "__init__.py":
            continue
        # Use src/ as root for files inside it; project root for everything else
        if has_src_layout and py_file.is_relative_to(src_dir):
            package_root = src_dir
        else:
            package_root = project_root
        try:
            modules.append(analyze_file(py_file, package_root=package_root))
        except SyntaxError:
            pass

    return modules
