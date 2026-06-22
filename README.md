# py-okf

A Python library for generating and managing [Open Knowledge Format (OKF)](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing) files from Python projects.

OKF is a vendor-neutral markdown specification that lets AI agents and humans access curated knowledge without vendor lock-in — a directory of `.md` files with YAML frontmatter, one file per concept (module, class, API, dataset, etc.).

`py-okf` analyzes your Python codebase using the `ast` module and generates an `.okf/` bundle of markdown files describing your project's concepts.

## Installation

```bash
pip install py-okf
```

## CLI Usage

```bash
# Generate OKF files for a Python project
okf generate /path/to/your/project

# Refresh stale OKF files (only regenerates files where source changed)
okf refresh /path/to/your/project

# Validate OKF files against the spec
okf validate /path/to/your/project

# Custom output directory
okf generate /path/to/your/project -o docs/okf

# Include private (underscore-prefixed) symbols
okf generate /path/to/your/project --include-private
```

## Python API

```python
from pyokf import analyze_project, generate_module_concepts, OKFBundle
from pathlib import Path

# Analyze a project
modules = analyze_project(Path("./myproject"))

# Generate OKF concepts
bundle = OKFBundle(Path("./.okf"))
bundle.ensure_directory()
for module in modules:
    concepts = generate_module_concepts(module)
    bundle.write_all(concepts)

# Load and validate an existing bundle
bundle = OKFBundle(Path("./.okf")).load()
errors = bundle.validate_directory()
```

## Generated Output

Running `okf generate .` produces an `.okf/` directory with flat, dotted-name files:

```
.okf/
├── mypackage.md                    # module concept
├── mypackage.Connection.md         # class concept
└── mypackage.query.md              # api concept (exported function)
```

Each file contains YAML frontmatter followed by a markdown description:

```markdown
---
type: api
title: mypackage.query
description: Execute a SQL query against the active connection.
resource: ./mypackage/__init__.py
tags:
- python
- api
timestamp: '2026-06-22T10:00:00Z'
---

# query

Execute a SQL query against the active connection.

## Signature

    def query(sql: str, params: Optional[list[str]] = None) -> list[dict]

## Parameters

- **`sql`**: `str`
- **`params`**: `Optional[list[str]]` *(default: `None`)*

## Returns

`list[dict]`
```

## Concept Types

| Type | Description |
|------|-------------|
| `module` | A Python module file |
| `class` | A class definition |
| `function` | A top-level function |
| `api` | A function listed in `__all__` (publicly exported) |

## Requirements

- Python 3.10+
- PyYAML >= 6.0
