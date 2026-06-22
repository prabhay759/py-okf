# py-okf

[![PyPI version](https://img.shields.io/pypi/v/py-okf.svg)](https://pypi.org/project/py-okf/)
[![Python versions](https://img.shields.io/pypi/pyversions/py-okf.svg)](https://pypi.org/project/py-okf/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**py-okf** is a Python library that generates [Open Knowledge Format (OKF)](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing) bundles from Python projects — making your codebase instantly readable by AI agents without any proprietary tooling.

---

## What is OKF?

The **Open Knowledge Format** (introduced by Google Cloud, June 2026) is a vendor-neutral markdown specification for representing organizational knowledge:

- A directory of `.md` files with YAML frontmatter
- Each file describes one **concept** (module, class, API, dataset, metric, etc.)
- Only the `type` field is required — everything else is optional
- Human- and AI-readable, no SDK or runtime required

```markdown
---
type: api
title: mypackage.query
description: Execute a SQL query.
resource: ./mypackage/db.py
tags: [python, api]
timestamp: '2026-06-22T10:00:00Z'
---

# query

Execute a SQL query against the active connection.
```

---

## What py-okf does

`py-okf` analyzes your Python project using the standard `ast` module and writes an `.okf/` bundle describing every public module, class, and function — with no imports, no runtime execution, and no external dependencies beyond PyYAML.

### Key features

| Feature | Detail |
|---|---|
| **Zero-import analysis** | Pure AST — never executes your code |
| **src/ layout aware** | Auto-detects `src/mypackage/` vs flat `mypackage/` |
| **`__all__` aware** | Marks exported functions as `type: api` |
| **Incremental refresh** | Re-generates only files whose source has changed |
| **Spec validation** | Checks all `.md` files against the OKF spec |
| **One dependency** | Only requires PyYAML |

---

## Installation

```bash
pip install py-okf
```

---

## Quick Start

```bash
# Generate an OKF bundle for your project
okf generate /path/to/your/project

# Only refresh files where source changed since last run
okf refresh /path/to/your/project

# Validate all .md files against the OKF spec
okf validate /path/to/your/project
```

This produces an `.okf/` directory:

```
.okf/
├── mypackage.md                    # module overview
├── mypackage.Connection.md         # class with attributes + methods
└── mypackage.query.md              # exported API function
```

---

## CLI Reference

| Command | Options | Description |
|---|---|---|
| `okf generate <PATH>` | `-o DIR`, `--include-private` | Generate full OKF bundle |
| `okf refresh <PATH>` | `-o DIR`, `--include-private` | Refresh stale files only |
| `okf validate <PATH>` | `-o DIR` | Validate bundle; exit 1 on errors |

---

## Python API Reference

| Symbol | Description |
|---|---|
| `analyze_file(path)` | Analyze one `.py` file → `ModuleInfo` |
| `analyze_project(root)` | Walk project → `list[ModuleInfo]` |
| `generate_module_concepts(module)` | Transform `ModuleInfo` → `list[OKFConcept]` |
| `generate_concept(concept)` | Render `OKFConcept` → markdown string |
| `OKFBundle(dir)` | Read/write/validate an `.okf/` directory |
| `ConceptType` | Enum: `module`, `class`, `function`, `api` |

```python
from pyokf import analyze_project, generate_module_concepts, OKFBundle
from pathlib import Path

modules = analyze_project(Path("./myproject"))
bundle = OKFBundle(Path("./.okf"))
bundle.ensure_directory()
for module in modules:
    bundle.write_all(generate_module_concepts(module))
```

---

## Concept Types Generated

| Type | When generated |
|---|---|
| `module` | One per `.py` file |
| `class` | One per class definition |
| `function` | Top-level non-exported functions |
| `api` | Functions listed in `__all__` |

---

## Requirements

- Python 3.10+
- PyYAML >= 6.0

---

## License

MIT — see [LICENSE](LICENSE)

## Links

- [GitHub Repository](https://github.com/prabhay759/py-okf)
- [PyPI Package](https://pypi.org/project/py-okf/)
- [OKF Specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
- [Report Issues](https://github.com/prabhay759/py-okf/issues)
