# Copyright (c) 2026, Masood Javid and contributors

import frappe
from frappe import _

from auto_parts.fitment.search import search_parts_by_vehicle


def _get_supersession_chain(item: str) -> list[str]:
	chain = []
	current = item
	visited = {item}

	while current:
		new_item = frappe.db.get_value(
			"Part Supersession",
			{"old_item": current, "is_active": 1},
			"new_item",
		)
		if not new_item:
			new_item = frappe.db.get_value("Item", current, "superseded_by")

		if not new_item or new_item in visited:
			break

		chain.append(new_item)
		visited.add(new_item)
		current = new_item

	return chain


@frappe.whitelist()
def get_smart_alternates(item: str, vehicle_configuration: str | None = None) -> dict:
	if not item:
		frappe.throw(_("Item is required."))

	supersession_chain = _get_supersession_chain(item)
	exclude = {item, *supersession_chain}

	fitment_alternates = []
	if vehicle_configuration:
		fitment_alternates = [
			row
			for row in search_parts_by_vehicle(vehicle_configuration=vehicle_configuration)
			if row.get("item") not in exclude and not row.get("disabled")
		]

	return {
		"item": item,
		"vehicle_configuration": vehicle_configuration,
		"supersession_chain": supersession_chain,
		"fitment_alternates": fitment_alternates,
	}
