# Copyright (c) 2026, Masood Javid and contributors

import os
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from auto_parts.auto_parts.doctype.aces_pies_import_batch.aces_pies_import_batch import (
	parse_import_file,
	promote_batch,
)
from auto_parts.catalog.reference_import import import_reference_csv
from auto_parts.catalog.resolver import enrich_aces_row, enrich_pies_row, lookup_part_terminology

SAMPLE_DIR = os.path.join(frappe.get_app_path("auto_parts"), "catalog", "sample_data")


def _read_sample(name):
	with open(os.path.join(SAMPLE_DIR, name), encoding="utf-8") as f:
		return f.read()


class TestCatalogReferenceImport(IntegrationTestCase):
	def setUp(self):
		patch("frappe.utils.global_search.sync_value_in_queue").start()
		patch("frappe.utils.global_search.update_global_search").start()
		self.addCleanup(patch.stopall)
		self._import_sample_references()

	def _import_sample_references(self):
		imports = [
			("PCdb Part Terminology", "sample_pcdb.csv"),
			("Qdb Qualifier", "sample_qdb.csv"),
			("VCdb Make", "sample_vcdb_make.csv"),
			("VCdb Model", "sample_vcdb_model.csv"),
			("VCdb Base Vehicle", "sample_vcdb_base_vehicle.csv"),
		]
		for reference_type, file_name in imports:
			results = import_reference_csv(reference_type, _read_sample(file_name))
			self.assertFalse(
				any(row["import_status"] == "Failed" for row in results),
				f"{file_name}: {results}",
			)
			self.assertTrue(results, file_name)

	def test_pcdb_lookup(self):
		term_id, term_name = lookup_part_terminology("10001")
		self.assertEqual(term_id, "10001")
		self.assertEqual(term_name, "Brake Pad Set")

	def test_enrich_pies_row_resolves_pcdb_id(self):
		row = enrich_pies_row({"part_terminology": "10001", "raw_sku": "AP-BRK-1001"})
		self.assertEqual(row["part_terminology_id"], "10001")
		self.assertEqual(row["part_terminology"], "Brake Pad Set")

	def test_enrich_aces_row_resolves_vcdb_and_qdb_ids(self):
		row = enrich_aces_row(
			{
				"raw_sku": "AP-BRK-1001",
				"base_vehicle_id": "5001",
				"make": "20",
				"model": "200",
				"qualifier_ids": "2853",
				"qty": 2,
			}
		)
		self.assertEqual(row["year"], 2018)
		self.assertEqual(row["make"], "Toyota")
		self.assertEqual(row["model"], "Camry")
		self.assertEqual(row["qualifiers"], "With 4 Wheel Drive")

	def test_aces_ids_xml_end_to_end(self):
		pies_batch = frappe.get_doc(
			{"doctype": "ACES PIES Import Batch", "import_type": "PIES", "status": "Draft"}
		).insert(ignore_permissions=True)
		self._attach(pies_batch, "sample_pies.xml", _read_sample("sample_pies.xml"))
		parse_import_file(pies_batch.name)
		promote_batch(pies_batch.name)

		aces_batch = frappe.get_doc(
			{"doctype": "ACES PIES Import Batch", "import_type": "ACES", "status": "Draft"}
		).insert(ignore_permissions=True)
		self._attach(aces_batch, "sample_aces_ids.xml", _read_sample("sample_aces_ids.xml"))
		parse_import_file(aces_batch.name)
		aces_batch.reload()
		line = aces_batch.import_lines[0]
		self.assertEqual(line.make, "Toyota")
		self.assertEqual(line.model, "Camry")
		self.assertEqual(line.qualifiers, "With 4 Wheel Drive")

		promote_batch(aces_batch.name)
		aces_batch.reload()
		self.assertEqual(aces_batch.import_lines[0].import_status, "Promoted")

	def _attach(self, batch, file_name, content):
		file_doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": file_name,
				"is_private": 1,
				"content": content,
				"attached_to_doctype": batch.doctype,
				"attached_to_name": batch.name,
			}
		).insert(ignore_permissions=True)
		batch.db_set("import_file", file_doc.file_url)
		batch.reload()
																																													