# Copyright (c) 2026, Masood Javid and contributors

import json

import frappe
from frappe import _
from frappe.utils import flt

from erpnext.stock.utils import scan_barcode

DOC_QTY_CONFIG = {
	"Pick List": {
		"table": "locations",
		"qty_field": "qty",
		"scanned_field": "picked_qty",
	},
	"Purchase Receipt": {
		"table": "items",
		"qty_field": "qty",
	},
	"Stock Entry": {
		"table": "items",
		"qty_field": "qty",
		"scanned_field": "qty",
	},
}


@frappe.whitelist()
def scan_item(search_value: str, doctype: str | None = None, docname: str | None = None, ctx=None):
	"""Resolve a barcode/serial/batch/warehouse scan and optionally validate qty on a document.

	Delegates item resolution to ERPNext core ``scan_barcode``. Adds document-level
	qty validation only when ``doctype`` and ``docname`` are supplied.
	"""
	if isinstance(ctx, str):
		ctx = json.loads(ctx)

	result = scan_barcode(search_value, ctx)
	if not result:
		return {"valid": False, "message": _("No Item, Serial No, Batch or Warehouse found")}

	if doctype and docname:
		result.update(get_document_qty_info(doctype, docname, result))

	result["valid"] = bool(result.get("item_code") or result.get("warehouse"))
	return result


def get_document_qty_info(doctype: str, docname: str, scan_result: dict) -> dict:
	item_code = scan_result.get("item_code")
	if not item_code:
		return {}

	config = DOC_QTY_CONFIG.get(doctype)
	if not config:
		return {}

	doc = frappe.get_doc(doctype, docname)
	matching_rows = [row for row in doc.get(config["table"]) if row.item_code == item_code]
	if not matching_rows:
		return {
			"on_document": False,
			"message": _("Item {0} is not on this {1}").format(item_code, doctype),
		}

	required_qty = sum(flt(row.get(config["qty_field"])) for row in matching_rows)
	scanned_field = config.get("scanned_field")

	if scanned_field:
		scanned_qty = sum(flt(row.get(scanned_field)) for row in matching_rows)
		remaining_qty = required_qty - scanned_qty
		return {
			"on_document": True,
			"required_qty": required_qty,
			"scanned_qty": scanned_qty,
			"remaining_qty": remaining_qty,
			"can_scan": remaining_qty > 0,
		}

	return {
		"on_document": True,
		"required_qty": required_qty,
		"can_scan": True,
	}
