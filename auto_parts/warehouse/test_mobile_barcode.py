# Copyright (c) 2026, Masood Javid and contributors

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from auto_parts.warehouse.barcode import get_document_qty_info, scan_item
from erpnext.stock.utils import scan_barcode


class TestMobileBarcode(IntegrationTestCase):
	def setUp(self):
		patch("frappe.utils.global_search.sync_value_in_queue").start()
		patch("frappe.utils.global_search.update_global_search").start()
		self.addCleanup(patch.stopall)

		self.company = frappe.db.get_single_value("Global Defaults", "default_company")
		self.warehouse = self._ensure_warehouse()
		self.item = self._ensure_item_with_barcode("AP-MOB-TEST-1", "AP-MOB-BAR-001")
		self._ensure_barcode_enabled()

	def _ensure_barcode_enabled(self):
		frappe.db.set_single_value("Stock Settings", "show_barcode_field", 1)

	def _ensure_warehouse(self):
		return frappe.db.get_value(
			"Warehouse", {"company": self.company, "is_group": 0}, "name", order_by="creation asc"
		)

	def _add_stock(self, item_code: str, qty: float = 10):
		from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry

		make_stock_entry(
			item_code=item_code,
			target=self.warehouse,
			qty=qty,
			rate=100,
			company=self.company,
		)

	def _ensure_item_with_barcode(self, item_code: str, barcode: str):
		if frappe.db.exists("Item", item_code):
			item = frappe.get_doc("Item", item_code)
		else:
			item = frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": item_code,
					"item_name": item_code,
					"item_group": frappe.db.get_value("Item Group", {"is_group": 0}, "name"),
					"stock_uom": "Nos",
					"is_stock_item": 1,
					"valuation_rate": 100,
				}
			).insert(ignore_permissions=True)

		if not any(row.barcode == barcode for row in item.get("barcodes", [])):
			item.append("barcodes", {"barcode": barcode})
			item.save(ignore_permissions=True)

		return item.name

	def test_core_scan_barcode_resolves_item(self):
		result = scan_barcode("AP-MOB-BAR-001")
		self.assertEqual(result["item_code"], self.item)

	def test_scan_item_api_resolves_barcode(self):
		result = scan_item("AP-MOB-BAR-001")
		self.assertTrue(result["valid"])
		self.assertEqual(result["item_code"], self.item)

	def test_scan_item_validates_pick_list_qty(self):
		self._add_stock(self.item, qty=10)
		pick_list = frappe.get_doc(
			{
				"doctype": "Pick List",
				"company": self.company,
				"purpose": "Delivery",
				"pick_manually": 1,
				"locations": [
					{
						"item_code": self.item,
						"qty": 5,
						"picked_qty": 2,
						"warehouse": self.warehouse,
						"stock_qty": 5,
						"conversion_factor": 1,
					}
				],
			}
		).insert(ignore_permissions=True)

		result = scan_item("AP-MOB-BAR-001", doctype="Pick List", docname=pick_list.name)
		self.assertTrue(result["on_document"])
		self.assertEqual(flt(result["required_qty"]), 5)
		self.assertEqual(flt(result["scanned_qty"]), 2)
		self.assertEqual(flt(result["remaining_qty"]), 3)
		self.assertTrue(result["can_scan"])

	def test_scan_item_rejects_unknown_item_on_pick_list(self):
		other_item = self._ensure_item_with_barcode("AP-MOB-TEST-2", "AP-MOB-BAR-002")
		self._add_stock(other_item, qty=5)
		pick_list = frappe.get_doc(
			{
				"doctype": "Pick List",
				"company": self.company,
				"purpose": "Delivery",
				"pick_manually": 1,
				"locations": [
					{
						"item_code": other_item,
						"qty": 3,
						"picked_qty": 0,
						"warehouse": self.warehouse,
						"stock_qty": 3,
						"conversion_factor": 1,
					}
				],
			}
		).insert(ignore_permissions=True)

		result = scan_item("AP-MOB-BAR-001", doctype="Pick List", docname=pick_list.name)
		self.assertFalse(result["on_document"])

	def test_receive_via_barcode_workflow(self):
		"""Simulate mobile receive: scan resolves item, qty can be applied on Purchase Receipt."""
		pr = frappe.get_doc(
			{
				"doctype": "Purchase Receipt",
				"company": self.company,
				"supplier": self._ensure_supplier(),
				"set_warehouse": self.warehouse,
				"items": [
					{
						"item_code": self.item,
						"qty": 4,
						"warehouse": self.warehouse,
						"rate": 100,
					}
				],
			}
		).insert(ignore_permissions=True)

		scan_result = scan_item(
			"AP-MOB-BAR-001",
			doctype="Purchase Receipt",
			docname=pr.name,
			ctx={"set_warehouse": self.warehouse, "company": self.company},
		)
		self.assertTrue(scan_result["valid"])
		self.assertTrue(scan_result["on_document"])
		self.assertTrue(scan_result["can_scan"])
		self.assertEqual(flt(scan_result["required_qty"]), 4)

		qty_info = get_document_qty_info("Purchase Receipt", pr.name, {"item_code": self.item})
		self.assertTrue(qty_info["on_document"])
		self.assertEqual(flt(qty_info["required_qty"]), 4)

	def test_pick_via_barcode_workflow(self):
		"""Simulate mobile pick: scan resolves item, picked_qty increments on Pick List."""
		self._add_stock(self.item, qty=10)
		pick_list = frappe.get_doc(
			{
				"doctype": "Pick List",
				"company": self.company,
				"purpose": "Delivery",
				"pick_manually": 1,
				"scan_mode": 1,
				"locations": [
					{
						"item_code": self.item,
						"qty": 6,
						"picked_qty": 0,
						"warehouse": self.warehouse,
						"stock_qty": 6,
						"conversion_factor": 1,
					}
				],
			}
		).insert(ignore_permissions=True)

		scan_result = scan_item("AP-MOB-BAR-001", doctype="Pick List", docname=pick_list.name)
		self.assertTrue(scan_result["can_scan"])

		pick_list.reload()
		pick_list.locations[0].picked_qty = flt(pick_list.locations[0].picked_qty) + 1
		pick_list.save(ignore_permissions=True)

		qty_info = get_document_qty_info("Pick List", pick_list.name, {"item_code": self.item})
		self.assertEqual(flt(qty_info["scanned_qty"]), 1)
		self.assertEqual(flt(qty_info["remaining_qty"]), 5)

	def _ensure_supplier(self):
		supplier = frappe.db.get_value("Supplier", {}, "name")
		if supplier:
			return supplier

		return frappe.get_doc(
			{
				"doctype": "Supplier",
				"supplier_name": "AP Mobile Test Supplier",
				"supplier_group": frappe.db.get_value("Supplier Group", {}, "name"),
			}
		).insert(ignore_permissions=True).name
