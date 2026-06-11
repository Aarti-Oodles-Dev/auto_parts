# Copyright (c) 2026, Masood Javid and contributors

import frappe
from frappe import _
from frappe.utils import cint


def resolve_vehicle_configuration(
	vehicle_configuration: str | None = None,
	year: int | None = None,
	make: str | None = None,
	model: str | None = None,
) -> str | None:
	if vehicle_configuration:
		return vehicle_configuration

	if year and make and model:
		return frappe.db.get_value(
			"Vehicle Configuration",
			{"year": cint(year), "make": make.strip(), "model": model.strip()},
			"name",
		)

	return None


@frappe.whitelist()
def search_parts_by_vehicle(
	vehicle_configuration: str | None = None,
	vehicle_garage: str | None = None,
	year: int | None = None,
	make: str | None = None,
	model: str | None = None,
	limit: int = 50,
) -> list[dict]:
	if not vehicle_configuration and vehicle_garage:
		from auto_parts.fitment.validation import resolve_vehicle_configuration_from_garage

		vehicle_configuration = resolve_vehicle_configuration_from_garage(vehicle_garage)

	vehicle_configuration = resolve_vehicle_configuration(vehicle_configuration, year, make, model)
	if not vehicle_configuration:
		frappe.throw(_("Vehicle Configuration is required."))

	limit = cint(limit) or 50
	fitments = frappe.get_all(
		"Part Fitment",
		filters={"vehicle_configuration": vehicle_configuration},
		fields=["name", "item", "position", "qty", "source"],
		order_by="modified desc",
		limit_page_length=limit,
	)

	results = []
	seen = set()
	for row in fitments:
		if row.item in seen:
			continue
		seen.add(row.item)

		item = frappe.db.get_value(
			"Item",
			row.item,
			["item_name", "manufacturer_part_number", "stock_uom", "disabled"],
			as_dict=True,
		) or {}

		results.append(
			{
				"fitment": row.name,
				"item": row.item,
				"item_name": item.get("item_name"),
				"manufacturer_part_number": item.get("manufacturer_part_number"),
				"stock_uom": item.get("stock_uom"),
				"position": row.position,
				"qty": row.qty,
				"source": row.source,
				"disabled": item.get("disabled"),
				"vehicle_configuration": vehicle_configuration,
			}
		)

	return results
