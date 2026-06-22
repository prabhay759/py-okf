"""OKF bundle reader, writer, and validator."""

from __future__ import annotations

import datetime
from pathlib import Path

import yaml

from pyokf.models import ConceptType, OKFConcept

REQUIRED_FRONTMATTER = frozenset({"type", "title", "description", "resource", "timestamp"})
VALID_TYPES = frozenset({t.value for t in ConceptType} | {
    "dataset", "metric", "playbook", "runbook", "table",
})


class ValidationError(Exception):
    """Raised when an OKF file fails validation."""


class OKFBundle:
    """Represents an OKF bundle directory (.okf/)."""

    def __init__(self, directory: Path) -> None:
        self.directory = Path(directory)
        self._concepts: dict[str, OKFConcept] = {}

    def load(self) -> "OKFBundle":
        """Load all .md files from the bundle directory."""
        if not self.directory.exists():
            return self
        for md_file in sorted(self.directory.glob("**/*.md")):
            try:
                concept = self._parse_file(md_file)
                rel = str(md_file.relative_to(self.directory))
                self._concepts[rel] = concept
            except (ValueError, yaml.YAMLError):
                pass
        return self

    def _parse_file(self, md_file: Path) -> OKFConcept:
        content = md_file.read_text(encoding="utf-8")
        if not content.startswith("---"):
            raise ValueError(f"Missing frontmatter in {md_file}")
        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ValueError(f"Malformed frontmatter in {md_file}")
        fm = yaml.safe_load(parts[1])
        if not isinstance(fm, dict):
            raise ValueError(f"Frontmatter is not a mapping in {md_file}")
        body = parts[2].strip()

        raw_ts = fm.get("timestamp")
        if isinstance(raw_ts, datetime.datetime):
            ts = raw_ts
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=datetime.timezone.utc)
        elif isinstance(raw_ts, str):
            ts = datetime.datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
        else:
            ts = datetime.datetime.now(tz=datetime.timezone.utc)

        raw_type = fm.get("type", "function")
        try:
            concept_type = ConceptType(raw_type)
        except ValueError:
            concept_type = ConceptType.FUNCTION

        known = {"type", "title", "description", "resource", "tags", "timestamp"}
        extra = {k: v for k, v in fm.items() if k not in known}

        return OKFConcept(
            type=concept_type,
            title=fm.get("title", ""),
            description=fm.get("description", ""),
            resource=fm.get("resource", ""),
            output_path=str(md_file.relative_to(self.directory)),
            tags=fm.get("tags", []),
            timestamp=ts,
            content=body,
            extra_frontmatter=extra,
        )

    def write(self, concept: OKFConcept, overwrite: bool = True) -> Path:
        """Write one OKFConcept to disk. Returns the path written to."""
        from pyokf.generator import generate_concept

        out_path = self.directory / concept.output_path
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if not overwrite and out_path.exists():
            return out_path

        out_path.write_text(generate_concept(concept), encoding="utf-8")
        self._concepts[concept.output_path] = concept
        return out_path

    def write_all(self, concepts: list[OKFConcept], overwrite: bool = True) -> list[Path]:
        """Write multiple concepts, returning paths written."""
        return [self.write(c, overwrite=overwrite) for c in concepts]

    def needs_refresh(self, concept: OKFConcept, source_mtime: float) -> bool:
        """Return True if the source file is newer than the existing OKF concept timestamp."""
        existing = self._concepts.get(concept.output_path)
        if existing is None:
            return True
        ts = existing.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=datetime.timezone.utc)
        source_dt = datetime.datetime.fromtimestamp(source_mtime, tz=datetime.timezone.utc)
        return source_dt > ts

    def validate_file(self, md_file: Path) -> list[str]:
        """Validate a single .md file against the OKF spec. Returns list of error strings."""
        errors: list[str] = []
        try:
            content = md_file.read_text(encoding="utf-8")
        except OSError as e:
            return [f"{md_file}: Cannot read file: {e}"]

        if not content.startswith("---"):
            return [f"{md_file}: Missing YAML frontmatter (file must start with ---)"]

        parts = content.split("---", 2)
        if len(parts) < 3:
            return [f"{md_file}: Malformed frontmatter (missing closing ---)"]

        try:
            fm = yaml.safe_load(parts[1])
        except yaml.YAMLError as e:
            return [f"{md_file}: Invalid YAML: {e}"]

        if not isinstance(fm, dict):
            return [f"{md_file}: Frontmatter must be a YAML mapping"]

        for field in sorted(REQUIRED_FRONTMATTER - set(fm.keys())):
            errors.append(f"{md_file}: Missing required field '{field}'")

        if "type" in fm and fm["type"] not in VALID_TYPES:
            errors.append(
                f"{md_file}: Invalid type '{fm['type']}'. "
                f"Must be one of: {sorted(VALID_TYPES)}"
            )

        return errors

    def validate_directory(self) -> dict[str, list[str]]:
        """Validate all .md files in the bundle directory. Returns filepath -> errors dict."""
        results: dict[str, list[str]] = {}
        if not self.directory.exists():
            return results
        for md_file in sorted(self.directory.glob("**/*.md")):
            errs = self.validate_file(md_file)
            if errs:
                results[str(md_file)] = errs
        return results

    @property
    def concepts(self) -> list[OKFConcept]:
        return list(self._concepts.values())

    def ensure_directory(self) -> None:
        """Create the bundle directory if it does not exist."""
        self.directory.mkdir(parents=True, exist_ok=True)
