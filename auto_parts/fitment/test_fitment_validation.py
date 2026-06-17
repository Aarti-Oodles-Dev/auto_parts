# Copyright (c) 2026, Masood Javid and contributors

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from auto_parts.fitment.alternates import get_smart_alternates
from auto_parts.fitment.search import search_parts_by_vehicle
from auto_parts.fitment.validation import (
	check_item_fitment,
	resolve_vehicle_configuration_from_garage,
	validate_sales_order_fitment,
)


class TestFitmentValidation(IntegrationTestCase):
	def setUp(self):
		patch("frappe.utils.global_search.sync_value_in_queue").start()
		patch("frappe.utils.global_search.update_global_search").start()
		self.addCleanup(patch.stopall)
		self.vehicle_config = self._ensure_vehicle_configuration()
		self.garage = self._ensure_vehicle_garage()
		self.fitting_item = self._ensure_item("AP-FIT-TEST-1")
		self.other_item = self._ensure_item("AP-FIT-TEST-2")
		self._ensure_fitment(self.fitting_item, self.vehicle_config)
		self._ensure_fitment(self.other_item, self._ensure_other_vehicle())

	def _ensure_vehicle_configuration(self):
		name = frappe.db.get_value(
			"Vehicle Configuration",
			{"year": 2018, "make": "Toyota", "model": "Camry"},
			"name",
		)
		if name:
			return name

		doc = frappe.get_doc(
			{
				"doctype": "Vehicle Configuration",
				"year": 2018,
				"make": "Toyota",
				"model": "Camry",
			}
		).insert(ignore_permissions=True)
		return doc.name

	def _ensure_other_vehicle(self):
		name = frappe.db.get_value(
			"Vehicle Configuration",
			{"year": 2015, "make": "Honda", "model": "Civic"},
			"name",
		)
		if name:
			return name

		doc = frappe.get_doc(
			{
				"doctype": "Vehicle Configuration",
				"year": 2015,
				"make": "Honda",
				"model": "Civic",
			}
		).insert(ignore_permissions=True)
		return doc.name

	def _ensure_vehicle_garage(self):
		customer = frappe.db.get_value("Customer", {"customer_name": "Fitment Test Customer"}, "name")
		if not customer:
			customer = frappe.get_doc(
				{"doctype": "Customer", "customer_name": "Fitment Test Customer", "customer_type": "Individual"}
			).insert(ignore_permissions=True).name

		name = frappe.db.get_value("Vehicle Garage", {"customer": customer, "make": "Toyota"}, "name")
		if name:
			frappe.db.set_value("Vehicle Garage", name, "vehicle_configuration", self.vehicle_config)
			return name

		doc = frappe.get_doc(
			{
				"doctype": "Vehicle Garage",
				"naming_series": "VG-.YYYY.-.#####",
				"customer": customer,
				"vehicle_configuration": self.vehicle_config,
				"year": 2018,
				"make": "Toyota",
				"model": "Camry",
			}
		).insert(ignore_permissions=True)
		return doc.name

	def _ensure_item(self, item_code):
		if frappe.db.exists("Item", item_code):
			return item_code

		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": item_code,
				"item_name": item_code,
				"item_group": "Products",
				"stock_uom": "Nos",
			}
		).insert(ignore_permissions=True)
		return item_code

	def _ensure_fitment(self, item, vehicle_configuration):
		if frappe.db.exists(
			"Part Fitment",
			{"item": item, "vehicle_configuration": vehicle_configuration},
		):
			return

		frappe.get_doc(
			{
				"doctype": "Part Fitment",
				"item": item,
				"vehicle_configuration": vehicle_configuration,
				"qty": 1,
				"source": "Manual",
			}
		).insert(ignore_permissions=True)

	def test_item_fits_selected_vehicle(self):
		result = check_item_fitment(self.fitting_item, self.vehicle_config)
		self.assertEqual(result["status"], "fits")
		self.assertTrue(result["fits"])

	def test_item_mismatch_when_fitment_exists_for_other_vehicle(self):
		result = check_item_fitment(self.other_item, self.vehicle_config)
		self.assertEqual(result["status"], "mismatch")
		self.assertFalse(result["fits"])

	def test_unknown_when_item_has_no_fitment_data(self):
		item = self._ensure_item("AP-FIT-TEST-UNKNOWN")
		result = check_item_fitment(item, self.vehicle_config)
		self.assertEqual(result["status"], "unknown")
		self.assertIsNone(result["fits"])

	def test_resolve_vehicle_configuration_from_garage(self):
		self.assertEqual(
			resolve_vehicle_configuration_from_garage(self.garage),
			self.vehicle_config,
		)

	def test_validate_sales_order_fitment_batch(self):
		results = validate_sales_order_fitment(
			vehicle_garage=self.garage,
			items=[self.fitting_item, self.other_item],
		)
		status_by_item = {row["item"]: row["status"] for row in results}
		self.assertEqual(status_by_item[self.fitting_item], "fits")
		self.assertEqual(status_by_item[self.other_item], "mismatch")

	def test_search_parts_by_vehicle_garage(self):
		rows = search_parts_by_vehicle(vehicle_garage=self.garage)
		items = {row["item"] for row in rows}
		self.assertIn(self.fitting_item, items)
		self.assertNotIn(self.other_item, items)

	def test_smart_alternates_for_vehicle(self):
		result = get_smart_alternates(self.other_item, vehicle_configuration=self.vehicle_config)
		alternate_items = {row["item"] for row in result["fitment_alternates"]}
		self.assertIn(self.fitting_item, alternate_items)
