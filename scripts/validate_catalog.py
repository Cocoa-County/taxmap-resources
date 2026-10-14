"""Validate reusable resource metadata without contacting external services."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlsplit

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
import yaml


ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = re.compile(r"\{apn(?:_display)?\}")
DOCUMENT_PATH = re.compile(r"\.(?:pdf|docx?|xlsx?|pptx?)(?:$|/)", re.IGNORECASE)
MEETING_PATH = re.compile(
    r"/(?:MinutesViewer\.php|AgendaViewer\.php|MediaPlayer\.php|"
    r"LegislationDetail\.aspx|MeetingDetail\.aspx|View\.ashx)(?:$|/)|"
    r"/services/legistar/download/", re.IGNORECASE,
)
PARCEL_KEYS = {"apn", "parcel", "parcelid", "parcel_id", "account", "accountnumber", "ain"}
MEETING_KEYS = {"clip_id", "meetingid", "meeting_id", "attachmentid", "attachment_id", "blobid"}


def validate_url(value: str, *, template: bool = False) -> None:
    parts = urlsplit(value)
    if (parts.scheme != "https" or not parts.hostname or parts.username is not None
            or parts.password is not None or any(char.isspace() for char in value)
            or "{" in parts.netloc or "}" in parts.netloc):
        raise ValueError("Use an absolute HTTPS URL with a fixed host and no credentials or whitespace")
    remainder = PLACEHOLDER.sub("", value)
    if "{" in remainder or "}" in remainder or bool(PLACEHOLDER.search(value)) != template:
        raise ValueError("Only tax-bill templates may use {apn} or {apn_display}; templates need a placeholder")
    if MEETING_PATH.search(parts.path) or (not template and DOCUMENT_PATH.search(parts.path)):
        raise ValueError("Store a reusable portal, not a specific document or meeting")
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key.casefold() in MEETING_KEYS:
            raise ValueError("Specific meeting/attachment query parameters are not catalog resources")
        if key.casefold() in PARCEL_KEYS and value:
            if not template or not PLACEHOLDER.fullmatch(value):
                raise ValueError("Concrete parcel/account URLs are not catalog resources")


def validate_document(document: dict, schema: dict) -> None:
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(document)
    for value in document["jurisdiction"].values():
        if value != value.strip():
            raise ValueError("Jurisdiction names must not have surrounding whitespace")
    ids = set()
    for resource in document["resources"]:
        if resource["id"] in ids:
            raise ValueError(f"Duplicate resource id: {resource['id']}")
        ids.add(resource["id"])
        for field in ("url", "url_template", "source_url"):
            if field in resource:
                validate_url(resource[field], template=field == "url_template")
        verification = resource["verification"]
        if date.fromisoformat(verification["checked_on"]) > date.today():
            raise ValueError("Verification dates cannot be in the future")
        for text in [resource["label"], resource["authority"], verification["method"], verification["notes"]]:
            if re.search(r"https?://", text, re.IGNORECASE):
                raise ValueError("Put URLs in dedicated URL fields, not free-text notes")
            if not text.strip():
                raise ValueError("Descriptions and verification text must not be blank")


def build_index(root: Path) -> tuple[dict, int]:
    schema = json.loads((root / "schema" / "resource.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    entries, jurisdiction_ids, jurisdictions, resource_ids = [], set(), set(), set()
    count = 0
    for path in sorted((root / "jurisdictions").rglob("*")):
        if path.is_dir():
            if path.is_symlink():
                raise ValueError("Catalog directories cannot be symlinks")
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Catalog files must stay inside the repository without symlinks")
        if path.suffix != ".yaml" or path.stat().st_size > 1024 * 1024:
            raise ValueError(f"Expected a small YAML metadata file: {path.relative_to(root)}")
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        try:
            validate_document(document, schema)
        except (ValidationError, ValueError) as error:
            raise ValueError(f"{path.relative_to(root)}: {error}") from error
        identity = tuple(sorted((key, value.casefold()) for key, value in document["jurisdiction"].items()))
        if document["id"] in jurisdiction_ids or identity in jurisdictions:
            raise ValueError(f"Duplicate jurisdiction: {document['id']}")
        jurisdiction_ids.add(document["id"])
        jurisdictions.add(identity)
        for resource in document["resources"]:
            if resource["id"] in resource_ids:
                raise ValueError(f"Resource id is not globally unique: {resource['id']}")
            resource_ids.add(resource["id"])
            count += 1
        entries.append({
            "id": document["id"], "path": path.relative_to(root).as_posix(),
            "jurisdiction": document["jurisdiction"],
            "kinds": sorted({resource["kind"] for resource in document["resources"]}),
        })
    if not entries:
        raise ValueError("The catalog needs at least one jurisdiction")
    return {"schema_version": 1, "jurisdictions": entries}, count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-index", action="store_true", help="Regenerate catalog.json after validating YAML")
    args = parser.parse_args()
    try:
        index, count = build_index(ROOT)
        destination = ROOT / "catalog.json"
        if args.write_index:
            destination.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        elif not destination.exists() or json.loads(destination.read_text(encoding="utf-8")) != index:
            raise ValueError("catalog.json is missing or stale; run with --write-index")
    except (OSError, ValueError, yaml.YAMLError) as error:
        parser.exit(1, f"Catalog validation failed: {error}\n")
    print(f"Validated {len(index['jurisdictions'])} jurisdictions and {count} reusable resources.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
