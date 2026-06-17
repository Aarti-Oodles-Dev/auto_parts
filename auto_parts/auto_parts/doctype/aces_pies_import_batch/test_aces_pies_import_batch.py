# Copyright (c) 2026, Masood Javid and Contributors
# See license.txt

import os

import frappe
from frappe.tests import IntegrationTestCase

from auto_parts.auto_parts.doctype.aces_pies_import_batch.aces_pies_import_batch import (
	parse_import_file,
	promote_batch,
)
from auto_parts.catalog import parser
from auto_parts.catalog.terminology import map_terminology_to_item_group

SAMPLE_DIR = os.path.join(
	frappe.get_app_path("auto_parts"), "catalog", "sample_data"
)


def _read_sample(name):
	with open(os.path.join(SAMPLE_DIR, name), encoding="utf-8") as f:
		return f.read()


class IntegrationTestACESPIESImportBatch(IntegrationTestCase):
	"""End-to-end import of the bundled ACES / PIES sample files."""

	def _attach(self, batch, file_name, content):
		file_doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": file_name,
				"is_private": 1,
				"content": content,
				"attached_to_doctype": "ACES PIES Import Batch",
				"attached_to_name": batch.name,
			}
		).insert(ignore_permissions=True)
		batch.db_set("import_file", file_doc.file_url)
		batch.reload()

	def test_pies_parser(self):
		rows = parser.parse_pies(_read_sample("sample_pies.xml"))
		self.assertEqual(len(rows), 2)
		self.assertEqual(rows[0]["raw_sku"], "AP-BRK-1001")
		self.assertEqual(rows[0]["part_terminology"], "Brake Pad Set")

	def test_aces_parser(self):
		rows = parser.parse_aces(_read_sample("sample_aces.xml"))
		self.assertEqual(len(rows), 2)
		self.assertEqual(rows[0]["raw_sku"], "AP-BRK-1001")
		self.assertEqual(rows[0]["make"], "Toyota")
		self.assertEqual(rows[0]["qty"], 2)
		self.assertEqual(rows[0]["qualifier_ids"], "2853")
		self.assertEqual(rows[0]["qualifiers"], "With 4 Wheel Drive (4)")
		self.assertEqual(rows[0]["aces_action"], "A")

	def test_pies_then_aces_end_to_end(self):
		# PIES: parse the file into staging and promote to Items.
		pies_batch = frappe.get_doc(
			{"doctype": "ACES PIES Import Batch", "import_type": "PIES", "status": "Draft"}
		).insert(ignore_permissions=True)
		self._attach(pies_batch, "sample_pies.xml", _read_sample("sample_pies.xml"))

		parse_import_file(pies_batch.name)
		pies_batch.reload()
		self.assertEqual(len(pies_batch.import_lines), 2)
		self.assertTrue(all(line.import_status == "Validated" for line in pies_batch.import_lines))

		promote_batch(pies_batch.name)
		pies_batch.reload()
		self.assertTrue(all(line.import_status == "Promoted" for line in pies_batch.import_lines))
		self.assertEqual(frappe.db.get_value("ACES PIES Import Batch", pies_batch.name, "status"), "Completed")

		item = frappe.get_doc("Item", "AP-BRK-1001")
		self.assertEqual(item.catalog_source, "ACES/PIES")
		self.assertEqual(item.aaia_brand_id, "ACME")
		self.assertTrue(frappe.db.exists("Item Group", "Brake Pad Set"))

		# ACES: parse the file into staging and promote to Part Fitment.
		aces_batch = frappe.get_doc(
			{"doctype": "ACES PIES Import Batch", "import_type": "ACES", "status": "Draft"}
		).insert(ignore_permissions=True)
		self._attach(aces_batch, "sample_aces.xml", _read_sample("sample_aces.xml"))

		parse_import_file(aces_batch.name)
		promote_batch(aces_batch.name)
		aces_batch.reload()
		self.assertTrue(all(line.import_status == "Promoted" for line in aces_batch.import_lines))

		fitment = frappe.get_all(
			"Part Fitment",
			filters={"item": "AP-BRK-1001", "source": "ACES/PIES"},
			fields=["name", "qty", "position", "vehicle_configuration", "qualifiers"],
		)
		self.assertEqual(len(fitment), 1)
		self.assertEqual(fitment[0].position, "Front")
		self.assertEqual(fitment[0].qualifiers, "With 4 Wheel Drive (4)")
		config = frappe.get_doc("Vehicle Configuration", fitment[0].vehicle_configuration)
		self.assertEqual(config.make, "Toyota")
		self.assertEqual(config.model, "Camry")

	def test_missing_item_is_reported_failed(self):
		batch = frappe.get_doc(
			{
				"doctype": "ACES PIES Import Batch",
				"import_type": "ACES",
				"status": "Draft",
				"import_lines": [
					{
						"raw_sku": "DOES-NOT-EXIST",
						"year": 2020,
						"make": "Honda",
						"model": "Civic",
						"qty": 1,
						"import_status": "Validated",
					}
				],
			}
		).insert(ignore_permissions=True)

		promote_batch(batch.name)
		batch.reload()
		self.assertEqual(batch.import_lines[0].import_status, "Failed")
		self.assertIn("not found", batch.import_lines[0].error_message)

	def test_duplicate_fitment_is_skipped(self):
		pies_batch = frappe.get_doc(
			{"doctype": "ACES PIES Import Batch", "import_type": "PIES", "status": "Draft"}
		).insert(ignore_permissions=True)
		self._attach(pies_batch, "sample_pies.xml", _read_sample("sample_pies.xml"))
		parse_import_file(pies_batch.name)
		promote_batch(pies_batch.name)

		aces_batch = frappe.get_doc(
			{"doctype": "ACES PIES Import Batch", "import_type": "ACES", "status": "Draft"}
		).insert(ignore_permissions=True)
		self._attach(aces_batch, "sample_aces.xml", _read_sample("sample_aces.xml"))
		parse_import_file(aces_batch.name)
		promote_batch(aces_batch.name)

		promote_batch(aces_batch.name)
		aces_batch.reload()
		self.assertTrue(all(line.import_status == "Skipped" for line in aces_batch.import_lines))

	def test_pcdb_mapping_is_used_for_item_group(self):
		frappe.get_doc(
			{
				"doctype": "PCdb Terminology Mapping",
				"part_terminology_id": "Brake Pad Set",
				"part_terminology_name": "Brake Pad Set",
				"item_group": "Products",
			}
		).insert(ignore_permissions=True)

		self.assertEqual(map_terminology_to_item_group("Brake Pad Set"), "Products")

	def test_aces_delete_action_is_skipped(self):
		rows = parser.parse_aces(
			"""<ACES><App action="D" id="99"><Part>AP-BRK-1001</Part></App></ACES>"""
		)
		self.assertEqual(rows[0]["aces_action"], "D")

		rows[0]["import_status"] = "Validated"
		batch = frappe.get_doc(
			{
				"doctype": "ACES PIES Import Batch",
				"import_type": "ACES",
				"status": "Draft",
				"import_lines": rows,
			}
		).insert(ignore_permissions=True)

		promote_batch(batch.name)
		batch.reload()
		self.assertEqual(batch.import_lines[0].import_status, "Skipped")
