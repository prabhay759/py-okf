"""OKF concept generator — converts analysis results to OKFConcept objects."""

from __future__ import annotations

import datetime
from typing import Optional

import yaml

from pyokf.models import (
    ClassInfo,
    ConceptType,
    FunctionInfo,
    MethodInfo,
    ModuleInfo,
    OKFConcept,
)


def _now_utc() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc)


def _okf_output_path(module_name: str, suffix: str = "") -> str:
    name = f"{module_name}.{suffix}" if suffix else module_name
    return f"{name}.md"


def _render_method_section(method: MethodInfo) -> str:
    prefix = "async " if method.is_async else ""
    lines = [f"### `{prefix}{method.signature}`"]
    if method.docstring:
        lines += ["", method.docstring]
    if method.decorators:
        lines += ["", f"**Decorators:** {', '.join(f'`@{d}`' for d in method.decorators)}"]
    return "\n".join(lines)


def generate_module_concept(module: ModuleInfo) -> OKFConcept:
    """Generate the OKF concept for the module-level file."""
    description = module.docstring or f"Python module: {module.name}"

    lines = [f"# {module.name}", ""]
    if module.docstring:
        lines += [module.docstring, ""]

    if module.classes:
        lines += ["## Classes", ""]
        for cls in module.classes:
            cls_path = _okf_output_path(module.name, cls.name)
            desc = f" — {cls.docstring.split(chr(10))[0]}" if cls.docstring else ""
            lines.append(f"- [`{cls.name}`]({cls_path}){desc}")
        lines.append("")

    pub_funcs = module.public_functions
    if pub_funcs:
        lines += ["## Functions", ""]
        for fn in pub_funcs:
            prefix = "async " if fn.is_async else ""
            exported_badge = " _(exported)_" if fn.is_exported else ""
            lines.append(f"- `{prefix}{fn.signature}`{exported_badge}")
            if fn.docstring:
                short_doc = fn.docstring.split("\n")[0]
                lines.append(f"  {short_doc}")
        lines.append("")

    return OKFConcept(
        type=ConceptType.MODULE,
        title=module.name,
        description=description,
        resource=f"./{module.source_file}",
        output_path=_okf_output_path(module.name),
        tags=["python", "module"],
        timestamp=_now_utc(),
        content="\n".join(lines),
    )


def generate_class_concept(cls: ClassInfo) -> OKFConcept:
    """Generate the OKF concept for a class."""
    description = cls.docstring or f"Python class: {cls.name}"

    lines = [f"# {cls.name}", ""]
    if cls.bases:
        lines += [f"**Inherits from:** {', '.join(f'`{b}`' for b in cls.bases)}", ""]
    if cls.decorators:
        lines += [f"**Decorators:** {', '.join(f'`@{d}`' for d in cls.decorators)}", ""]
    if cls.docstring:
        lines += [cls.docstring, ""]

    if cls.attributes:
        lines += ["## Attributes", ""]
        for attr in cls.attributes:
            ann = f": {attr.annotation}" if attr.annotation else ""
            default = f" = {attr.default}" if attr.default is not None else ""
            lines.append(f"- `{attr.name}{ann}{default}`")
        lines.append("")

    init = next((m for m in cls.methods if m.name == "__init__"), None)
    if init:
        lines += ["## Constructor", "", _render_method_section(init), ""]

    public_non_init = [m for m in cls.public_methods if m.name != "__init__"]
    if public_non_init:
        lines += ["## Methods", ""]
        for method in public_non_init:
            lines += [_render_method_section(method), ""]

    dunder_non_init = [m for m in cls.dunder_methods if m.name != "__init__"]
    if dunder_non_init:
        lines += ["## Special Methods", ""]
        for method in dunder_non_init:
            lines += [_render_method_section(method), ""]

    return OKFConcept(
        type=ConceptType.CLASS,
        title=f"{cls.module_name}.{cls.name}",
        description=description,
        resource=f"./{cls.source_file}",
        output_path=_okf_output_path(cls.module_name, cls.name),
        tags=["python", "class"],
        timestamp=_now_utc(),
        content="\n".join(lines),
    )


def generate_function_concept(fn: FunctionInfo) -> OKFConcept:
    """Generate the OKF concept for a top-level function."""
    description = fn.docstring or f"Python function: {fn.name}"
    concept_type = fn.concept_type

    prefix = "async " if fn.is_async else ""
    lines = [f"# {fn.name}", ""]
    if fn.docstring:
        lines += [fn.docstring, ""]

    lines += ["## Signature", "", "```python", f"{prefix}{fn.signature}", "```", ""]

    if fn.args:
        lines += ["## Parameters", ""]
        for arg in fn.args:
            ann = f": `{arg.annotation}`" if arg.annotation else ""
            default = f" *(default: `{arg.default}`)*" if arg.default is not None else ""
            kind_note = ""
            if arg.kind == "keyword_only":
                kind_note = " *(keyword-only)*"
            elif arg.kind == "var_positional":
                kind_note = " *(variadic)*"
            elif arg.kind == "var_keyword":
                kind_note = " *(keyword variadic)*"
            lines.append(f"- **`{arg.name}`**{ann}{default}{kind_note}")
        lines.append("")

    if fn.returns:
        lines += ["## Returns", "", f"`{fn.returns}`", ""]

    if fn.decorators:
        lines += ["## Decorators", ""]
        for d in fn.decorators:
            lines.append(f"- `@{d}`")
        lines.append("")

    return OKFConcept(
        type=concept_type,
        title=f"{fn.module_name}.{fn.name}",
        description=description,
        resource=f"./{fn.source_file}",
        output_path=_okf_output_path(fn.module_name, fn.name),
        tags=["python", concept_type.value],
        timestamp=_now_utc(),
        content="\n".join(lines),
    )


def generate_module_concepts(
    module: ModuleInfo,
    include_private: bool = False,
    generate_functions: bool = True,
    generate_classes: bool = True,
) -> list[OKFConcept]:
    """Generate all OKF concepts for a module and its contents."""
    concepts: list[OKFConcept] = [generate_module_concept(module)]

    if generate_classes:
        for cls in module.classes:
            concepts.append(generate_class_concept(cls))

    if generate_functions:
        for fn in module.functions:
            if include_private or fn.is_public:
                concepts.append(generate_function_concept(fn))

    return concepts


def generate_concept(concept: OKFConcept) -> str:
    """Render an OKFConcept to its full markdown string (frontmatter + body)."""
    frontmatter: dict = {
        "type": concept.type.value,
        "title": concept.title,
        "description": concept.description,
        "resource": concept.resource,
        "tags": concept.tags,
        "timestamp": concept.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    frontmatter.update(concept.extra_frontmatter)

    fm_str = yaml.dump(
        frontmatter,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    return f"---\n{fm_str}---\n\n{concept.content.strip()}\n"
