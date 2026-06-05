# Copyright (c) 2026, Masood Javid and contributors

import frappe
from frappe import _


def validate_item_cross_references(doc, method=None):
	seen = set()

	for row in doc.get("item_cross_references", []):
		part_number = (row.part_number or "").strip().upper()
		if not part_number:
			frappe.throw(_("Part Number is required in Cross References."))

		row.part_number = part_number
		brand_name = (row.brand_name or "").strip()
		row.brand_name = brand_name

		key = (row.reference_type, brand_name.lower(), part_number)
		if key in seen:
			frappe.throw(
				_("Duplicate cross reference for {0} / {1} / {2}.").format(
					row.reference_type, brand_name or "-", part_number
				)
			)
		seen.add(key)
