# Copyright (c) 2026, Masood Javid and contributors

"""Import marketplace orders into ERPNext Sales Orders."""

import frappe
from frappe import _
from frappe.utils import flt, getdate


def _get_marketplace_customer(channel_name: str) -> str:
	customer_name = f"Marketplace - {channel_name}"
	if frappe.db.exists("Customer", customer_name):
		return customer_name

	customer_group = frappe.db.get_value("Customer Group", {"is_group": 0}, "name")
	if not customer_group:
		customer_group = frappe.db.get_single_value("Selling Settings", "customer_group")

	doc = frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": customer_name,
			"customer_type": "Company",
			"customer_group": customer_group,
			"territory": frappe.db.get_single_value("Selling Settings", "territory") or "All Territories",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def import_marketplace_order(order: dict, channel_name: str) -> str | None:
	"""Create a Sales Order from a normalized marketplace order payload.

	Expected order keys:
	    external_order_id, order_date, items: [{item_code, qty, rate}],
	    customer_name (optional), shipping_address (optional)
	"""
	external_id = order.get("external_order_id")
	if not external_id:
		return None

	if frappe.db.exists("Sales Order", {"marketplace_order_id": external_id}):
		return frappe.db.get_value("Sales Order", {"marketplace_order_id": external_id}, "name")

	items = order.get("items") or []
	if not items:
		write_import_log(channel_name, external_id, "Failed", _("No line items in marketplace order."))
		return None

	company = frappe.defaults.get_global_default("company")
	if not company:
		company = frappe.db.get_single_value("Global Defaults", "default_company")
	if not company:
		write_import_log(channel_name, external_id, "Failed", _("No default company configured."))
		return None

	customer = _get_marketplace_customer(channel_name)
	so = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"customer": customer,
			"company": company,
			"transaction_date": getdate(order.get("order_date")),
			"delivery_date": getdate(order.get("order_date")),
			"marketplace_order_id": external_id,
			"marketplace_channel": channel_name,
			"items": [],
		}
	)

	for row in items:
		item_code = row.get("item_code")
		if not item_code or not frappe.db.exists("Item", item_code):
			write_import_log(
				channel_name,
				external_id,
				"Failed",
				_("Item {0} not found for marketplace order.").format(item_code),
			)
			return None
		so.append(
			"items",
			{
				"item_code": item_code,
				"qty": flt(row.get("qty") or 1),
				"rate": flt(row.get("rate") or 0),
			},
		)

	so.insert(ignore_permissions=True)
	write_import_log(channel_name, external_id, "Success", _("Sales Order {0} created.").format(so.name))
	return so.name


def write_import_log(channel_name: str, external_order_id: str, status: str, message: str):
	from auto_parts.marketplace.sync_log import write_sync_log

	write_sync_log(
		listing_name=None,
		channel_name=channel_name,
		direction="Inbound",
		status=status,
		message=f"{external_order_id}: {message}",
	)
