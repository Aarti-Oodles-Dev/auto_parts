# Copyright (c) 2026, Masood Javid and contributors

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from auto_parts.marketplace.factory import get_connector
from auto_parts.marketplace.oversell import get_available_qty
from auto_parts.marketplace.pricing import calculate_listing_price
from auto_parts.marketplace.sync_engine import sync_listing
from auto_parts.marketplace.order_import import import_marketplace_order


class TestMarketplaceSync(IntegrationTestCase):
	def setUp(self):
		patch("frappe.utils.global_search.sync_value_in_queue").start()
		patch("frappe.utils.global_search.update_global_search").start()
		self.addCleanup(patch.stopall)

		self._ensure_settings()
		self.item = self._ensure_item("AP-MKT-TEST-1")
		self.warehouse = self._ensure_warehouse()
		self._ensure_channel("eBay", self.warehouse)
		self.listing = self._ensure_listing()

	def _ensure_settings(self):
		settings = frappe.get_single("Auto Parts Settings")
		settings.enable_marketplace_sync = 1
		settings.default_stock_reserve_percent = 10
		settings.save(ignore_permissions=True)

	def _ensure_item(self, item_code: str):
		if frappe.db.exists("Item", item_code):
			frappe.db.set_value("Item", item_code, "valuation_rate", 100)
			return item_code

		doc = frappe.get_doc(
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
		return doc.name

	def _ensure_warehouse(self):
		company = frappe.db.get_single_value("Global Defaults", "default_company")
		name = frappe.db.get_value("Warehouse", {"company": company, "is_group": 0}, "name")
		return name

	def _ensure_channel(self, channel_name: str, warehouse: str):
		if frappe.db.exists("Marketplace Channel", channel_name):
			doc = frappe.get_doc("Marketplace Channel", channel_name)
		else:
			doc = frappe.get_doc(
				{"doctype": "Marketplace Channel", "channel_name": channel_name}
			)
		doc.enabled = 1
		doc.default_warehouse = warehouse
		doc.seller_id = "TEST-SELLER"
		doc.api_key = "test-key"
		doc.flags.ignore_permissions = True
		doc.save()

	def _ensure_listing(self):
		existing = frappe.db.get_value(
			"Marketplace Listing",
			{"item": self.item, "marketplace_channel": "eBay"},
			"name",
		)
		if existing:
			frappe.db.set_value("Marketplace Listing", existing, "listing_status", "Active")
			return existing

		doc = frappe.get_doc(
			{
				"doctype": "Marketplace Listing",
				"item": self.item,
				"marketplace_channel": "eBay",
				"listing_status": "Active",
				"pricing_method": "Cost Plus",
				"channel_markup_percent": 20,
				"external_listing_id": "EBAY-TEST-1",
			}
		).insert(ignore_permissions=True)
		return doc.name

	def test_cost_plus_pricing(self):
		listing = frappe.get_doc("Marketplace Listing", self.listing)
		price = calculate_listing_price(listing)
		self.assertEqual(price, 120.0)

	def test_oversell_reserve(self):
		self.assertTrue(self.warehouse)
		with patch("auto_parts.marketplace.oversell.get_stock_balance", return_value=100):
			qty = get_available_qty(self.item, self.warehouse, qty_buffer=5, reserve_percent=10)
		self.assertEqual(qty, 85)

	def test_ebay_connector_dry_run(self):
		connector = get_connector("eBay")
		result = connector.test_connection()
		self.assertTrue(result["success"])
		self.assertTrue(result.get("simulated"))

	def test_sync_listing_writes_log(self):
		with patch("erpnext.stock.utils.get_stock_balance", return_value=50):
			result = sync_listing(self.listing)
		self.assertTrue(result["success"])
		log_count = frappe.db.count(
			"Marketplace Sync Log",
			{"marketplace_listing": self.listing, "sync_direction": "Outbound"},
		)
		self.assertGreater(log_count, 0)

	def test_import_marketplace_order(self):
		order = {
			"external_order_id": "MKT-ORD-TEST-1",
			"order_date": frappe.utils.today(),
			"items": [{"item_code": self.item, "qty": 1, "rate": 120}],
		}
		so_name = import_marketplace_order(order, "eBay")
		self.assertTrue(so_name)
		self.assertTrue(frappe.db.exists("Sales Order", so_name))
		self.assertEqual(
			frappe.db.get_value("Sales Order", so_name, "marketplace_order_id"),
			"MKT-ORD-TEST-1",
		)
