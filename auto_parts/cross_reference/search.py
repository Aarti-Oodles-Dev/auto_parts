# Copyright (c) 2026, Masood Javid and contributors

import frappe
from frappe import _


@frappe.whitelist()
def search_item_by_cross_reference(
	part_number: str,
	reference_type: str | None = None,
	brand_name: str | None = None,
) -> list[dict]:
	part_number = (part_number or "").strip().upper()
	if not part_number:
		frappe.throw(_("Part Number is required."))

	filters = {
		"part_number": part_number,
		"parenttype": "Item",
		"parentfield": "item_cross_references",
	}
	if reference_type:
		filters["reference_type"] = reference_type
	if brand_name:
		filters["brand_name"] = brand_name.strip()

	rows = frappe.get_all(
		"Item Cross Reference",
		filters=filters,
		fields=["parent", "reference_type", "brand_name", "part_number", "notes"],
		order_by="modified desc",
	)

	results = []
	seen = set()
	for row in rows:
		if row.parent in seen:
			continue
		seen.add(row.parent)

		item = frappe.db.get_value(
			"Item",
			row.parent,
			["item_name", "manufacturer_part_number", "disabled"],
			as_dict=True,
		) or {}

		results.append(
			{
				"item": row.parent,
				"item_name": item.get("item_name"),
				"manufacturer_part_number": item.get("manufacturer_part_number"),
				"reference_type": row.reference_type,
				"brand_name": row.brand_name,
				"part_number": row.part_number,
				"notes": row.notes,
				"disabled": item.get("disabled"),
			}
		)

	return results
