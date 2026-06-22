"""Tests for pyokf.cli."""

import sys
from pathlib import Path

import pytest

from pyokf.bundle import OKFBundle
from pyokf.cli import main


def run_cli(*args):
    """Run CLI and return exit code."""
    with pytest.raises(SystemExit) as exc_info:
        main(list(args))
    return exc_info.value.code


def test_generate_creates_okf_directory(sample_project):
    code = run_cli("generate", str(sample_project))
    assert code == 0
    okf_dir = sample_project / ".okf"
    assert okf_dir.is_dir()


def test_generate_creates_md_files(sample_project):
    run_cli("generate", str(sample_project))
    okf_dir = sample_project / ".okf"
    md_files = list(okf_dir.glob("*.md"))
    assert len(md_files) > 0


def test_generate_output_is_valid_bundle(sample_project):
    run_cli("generate", str(sample_project))
    bundle = OKFBundle(sample_project / ".okf").load()
    assert len(bundle.concepts) > 0


def test_generate_custom_output_dir(sample_project, tmp_path):
    custom_dir = tmp_path / "my_okf"
    code = run_cli("generate", str(sample_project), "-o", str(custom_dir))
    assert code == 0
    assert custom_dir.is_dir()
    assert len(list(custom_dir.glob("*.md"))) > 0


def test_generate_include_private(sample_project):
    run_cli("generate", str(sample_project), "--include-private")
    okf_dir = sample_project / ".okf"
    all_names = [f.name for f in okf_dir.glob("*.md")]
    assert any("_helper" in n for n in all_names)


def test_generate_excludes_private_by_default(sample_project):
    run_cli("generate", str(sample_project))
    okf_dir = sample_project / ".okf"
    all_names = [f.name for f in okf_dir.glob("*.md")]
    assert not any("_helper" in n for n in all_names)


def test_generate_nonexistent_path():
    code = run_cli("generate", "/nonexistent/path/abc123")
    assert code == 1


def test_validate_valid_bundle(sample_project):
    run_cli("generate", str(sample_project))
    code = run_cli("validate", str(sample_project))
    assert code == 0


def test_validate_invalid_bundle(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    run_cli("generate", str(tmp_path))

    # Corrupt one file
    okf_dir = tmp_path / ".okf"
    first_md = next(okf_dir.glob("*.md"))
    first_md.write_text("# No frontmatter at all\n", encoding="utf-8")

    code = run_cli("validate", str(tmp_path))
    assert code == 1


def test_validate_missing_okf_dir(tmp_path):
    code = run_cli("validate", str(tmp_path))
    assert code == 1


def test_refresh_skips_up_to_date(sample_project, capsys):
    run_cli("generate", str(sample_project))
    run_cli("refresh", str(sample_project))
    captured = capsys.readouterr()
    assert "skipped" in captured.out


def test_refresh_regenerates_stale(sample_project, tmp_path):
    import time

    run_cli("generate", str(sample_project))
    okf_dir = sample_project / ".okf"

    # Touch a source file to make it newer than the OKF
    time.sleep(0.05)
    src_file = sample_project / "mypackage" / "utils.py"
    src_file.touch()

    run_cli("refresh", str(sample_project))
    # Should complete without error; stale files are re-generated


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "0.1.0" in captured.out
