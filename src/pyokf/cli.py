"""CLI entry point for py-okf."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pyokf.analyzer import analyze_project
from pyokf.bundle import OKFBundle
from pyokf.generator import generate_module_concepts


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", metavar="PATH", help="Path to the Python project root")
    parser.add_argument(
        "-o", "--output",
        default=".okf",
        metavar="DIR",
        help="Output directory for OKF files (default: .okf)",
    )


def cmd_generate(args: argparse.Namespace) -> int:
    project_root = Path(args.path).resolve()
    if not project_root.exists():
        print(f"error: path does not exist: {project_root}", file=sys.stderr)
        return 1

    okf_dir = (project_root / args.output).resolve()
    bundle = OKFBundle(okf_dir)
    bundle.ensure_directory()

    include_private = getattr(args, "include_private", False)
    modules = analyze_project(project_root, include_private=include_private)

    if not modules:
        print(f"No Python files found in: {project_root}")
        return 0

    total = 0
    for module in modules:
        concepts = generate_module_concepts(module, include_private=include_private)
        paths = bundle.write_all(concepts)
        for p in paths:
            print(f"  generated: {p.relative_to(project_root)}")
        total += len(paths)

    print(f"\nGenerated {total} OKF file(s) in {okf_dir.relative_to(project_root)}/")
    return 0


def cmd_refresh(args: argparse.Namespace) -> int:
    project_root = Path(args.path).resolve()
    if not project_root.exists():
        print(f"error: path does not exist: {project_root}", file=sys.stderr)
        return 1

    okf_dir = (project_root / args.output).resolve()
    bundle = OKFBundle(okf_dir).load()

    include_private = getattr(args, "include_private", False)
    modules = analyze_project(project_root, include_private=include_private)

    refreshed = 0
    skipped = 0
    for module in modules:
        source_mtime = (project_root / module.source_file).stat().st_mtime
        concepts = generate_module_concepts(module, include_private=include_private)
        for concept in concepts:
            if bundle.needs_refresh(concept, source_mtime):
                bundle.write(concept, overwrite=True)
                print(f"  refreshed: {concept.output_path}")
                refreshed += 1
            else:
                skipped += 1

    print(f"\nRefreshed {refreshed}, skipped {skipped} (up-to-date) OKF file(s).")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    project_root = Path(args.path).resolve()
    okf_dir = (project_root / args.output).resolve()

    if not okf_dir.exists():
        print(f"error: OKF directory does not exist: {okf_dir}", file=sys.stderr)
        return 1

    bundle = OKFBundle(okf_dir)
    results = bundle.validate_directory()

    if not results:
        total = len(list(okf_dir.glob("**/*.md")))
        print(f"All {total} OKF file(s) are valid.")
        return 0

    total_errors = 0
    for errors in results.values():
        for err in errors:
            print(f"  {err}", file=sys.stderr)
            total_errors += 1

    print(f"\n{total_errors} validation error(s) found.", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="okf",
        description="py-okf: Generate and manage Open Knowledge Format (OKF) files for Python projects.",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    gen_parser = subparsers.add_parser("generate", help="Generate OKF files from Python source")
    _add_common_args(gen_parser)
    gen_parser.add_argument(
        "--include-private",
        action="store_true",
        help="Include private (underscore-prefixed) symbols",
    )
    gen_parser.set_defaults(func=cmd_generate)

    ref_parser = subparsers.add_parser("refresh", help="Refresh stale OKF files")
    _add_common_args(ref_parser)
    ref_parser.add_argument("--include-private", action="store_true")
    ref_parser.set_defaults(func=cmd_refresh)

    val_parser = subparsers.add_parser("validate", help="Validate OKF files against the spec")
    _add_common_args(val_parser)
    val_parser.set_defaults(func=cmd_validate)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
