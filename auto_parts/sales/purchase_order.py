# Copyright (c) 2026, Masood Javid and contributors

import frappe
from frappe import _
from frappe.utils import cint


def validate_purchase_order(doc, method=None):
	if not doc.get("linked_sales_order"):
		return

	so = frappe.db.get_value(
		"Sales Order",
		doc.linked_sales_order,
		["is_special_order", "is_buyout", "customer"],
		as_dict=True,
	)

	if not so:
		frappe.throw(_("Linked Sales Order {0} does not exist.").format(doc.linked_sales_order))

	if cint(doc.get("is_buyout_po")) and not so.is_buyout:
		frappe.throw(
			_("Sales Order {0} must have Is Buyout enabled for a Buyout Purchase Order.").format(
				doc.linked_sales_order
			)
		)

	if not cint(doc.get("is_buyout_po")) and so.is_buyout and not so.is_special_order:
		frappe.throw(
			_("Buyout Sales Order {0} requires a Buyout Purchase Order (Is Buyout PO).").format(
				doc.linked_sales_order
			)
		)
