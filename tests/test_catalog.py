import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from jsonschema import ValidationError
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_catalog", ROOT / "scripts" / "validate_catalog.py")
catalog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(catalog)


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads((ROOT / "schema" / "resource.schema.json").read_text(encoding="utf-8"))
        self.document = yaml.safe_load(
            (ROOT / "jurisdictions" / "us" / "ca" / "contra-costa" / "county.yaml").read_text(encoding="utf-8"))

    def test_repository_and_generated_index(self):
        index, count = catalog.build_index(ROOT)
        self.assertGreaterEqual(count, 10)
        self.assertEqual(index, json.loads((ROOT / "catalog.json").read_text(encoding="utf-8")))
        catalog.validate_document(self.document, self.schema)

    def test_rejects_specific_documents_and_parcels(self):
        urls = [
            "https://example.gov/reports/adopted.pdf",
            "https://example.gov/MinutesViewer.php?clip_id=123",
            "https://example.gov/MeetingDetail.aspx?ID=123",
            "https://example.gov/services/legistar/download/pdf/123/report",
            "https://example.gov/lookup?APN=123-456-789",
            "https://example.gov/archive?attachment_id=123",
        ]
        for url in urls:
            with self.subTest(url=url), self.assertRaises(ValueError):
                catalog.validate_url(url)

    def test_allows_reusable_entry_points_and_templates(self):
        for url in [
            "https://example.gov/",
            "https://example.gov/ViewPublisher.php?view_id=2",
            "https://example.gov/Calendar.aspx",
            "https://example.gov/arcgis/rest/services/Parcels/MapServer/0?f=json",
            "https://example.gov/data/parcels.geojson",
        ]:
            with self.subTest(url=url):
                catalog.validate_url(url)
        catalog.validate_url("https://example.gov/bill?APN={apn_display}", template=True)
        catalog.validate_url("https://example.gov/bill/{apn}.pdf", template=True)

    def test_rejects_unsafe_or_invalid_templates(self):
        for url in [
            "http://example.gov/bill?APN={apn}",
            "https://{apn}.example.gov/bill",
            "https://user:password@example.gov/bill?APN={apn}",
            "https://example.gov/bill?APN={owner}",
            "https://example.gov/bill?APN=123&other={apn}",
            "https://example.gov/bill",
            "https://example.gov/bill with spaces?APN={apn}",
        ]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                catalog.validate_url(url, template=True)

    def test_rejects_duplicate_resources_and_unknown_fields(self):
        duplicate = copy.deepcopy(self.document)
        duplicate["resources"].append(copy.deepcopy(duplicate["resources"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate resource"):
            catalog.validate_document(duplicate, self.schema)
        self.document["credentials"] = "not permitted"
        with self.assertRaises(ValidationError):
            catalog.validate_document(self.document, self.schema)

    def test_validates_verification_and_all_url_fields(self):
        for change in [
            {"source_url": "https://example.gov/meeting/report.pdf"},
            {"verification": {"status": "verified", "checked_on": "not-a-date", "method": "check", "notes": "notes"}},
            {"verification": {"status": "verified", "checked_on": "2026-10-14", "method": "check", "notes": "https://example.gov/report.pdf"}},
        ]:
            document = copy.deepcopy(self.document)
            document["resources"][0].update(change)
            with self.subTest(change=change), self.assertRaises((ValueError, ValidationError)):
                catalog.validate_document(document, self.schema)

    def test_tax_templates_need_apn_format_and_year_behavior(self):
        resource = next(item for item in self.document["resources"] if "url_template" in item)
        for field in ["apn_format", "year_behavior"]:
            document = copy.deepcopy(self.document)
            item = next(row for row in document["resources"] if row["id"] == resource["id"])
            del item[field]
            with self.subTest(field=field), self.assertRaises(ValidationError):
                catalog.validate_document(document, self.schema)

    def test_duplicate_jurisdictions_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "schema").mkdir()
            shutil.copyfile(ROOT / "schema" / "resource.schema.json", root / "schema" / "resource.schema.json")
            (root / "jurisdictions").mkdir()
            for name in ("first.yaml", "second.yaml"):
                (root / "jurisdictions" / name).write_text(yaml.safe_dump(self.document), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate jurisdiction"):
                catalog.build_index(root)

    def test_city_does_not_require_a_county(self):
        self.document["jurisdiction"] = {"country": "US", "region": "VA", "city": "Alexandria"}
        catalog.validate_document(self.document, self.schema)

    def test_rejects_downloaded_files_in_catalog(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "schema").mkdir()
            shutil.copyfile(ROOT / "schema" / "resource.schema.json", root / "schema" / "resource.schema.json")
            (root / "jurisdictions").mkdir()
            (root / "jurisdictions" / "report.pdf").write_bytes(b"not catalog metadata")
            with self.assertRaisesRegex(ValueError, "small YAML"):
                catalog.build_index(root)


if __name__ == "__main__":
    unittest.main()
