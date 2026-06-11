# Copyright (c) 2026, Masood Javid and contributors

import json

import frappe
from frappe import _

from auto_parts.fitment.search import resolve_vehicle_configuration


def resolve_vehicle_configuration_from_garage(vehicle_garage: str | None) -> str | None:
	if not vehicle_garage:
		return None

	garage = frappe.db.get_value(
		"Vehicle Garage",
		vehicle_garage,
		["vehicle_configuration", "year", "make", "model"],
		as_dict=True,
	)
	if not garage:
		return None

	return resolve_vehicle_configuration(
		garage.vehicle_configuration,
		garage.year,
		garage.make,
		garage.model,
	)


def check_item_fitment(item: str, vehicle_configuration: str | None) -> dict:
	"""Return fitment status for one item against a vehicle configuration."""
	if not vehicle_configuration:
		return {
			"item": item,
			"vehicle_configuration": None,
			"status": "no_vehicle",
			"fits": None,
			"message": _("No vehicle selected."),
		}

	fits = bool(
		frappe.db.exists(
			"Part Fitment",
			{"item": item, "vehicle_configuration": vehicle_configuration},
		)
	)
	if fits:
		return {
			"item": item,
			"vehicle_configuration": vehicle_configuration,
			"status": "fits",
			"fits": True,
			"message": "",
		}

	if frappe.db.exists("Part Fitment", {"item": item}):
		return {
			"item": item,
			"vehicle_configuration": vehicle_configuration,
			"status": "mismatch",
			"fits": False,
			"message": _("This part is not listed for the selected vehicle."),
		}

	return {
		"item": item,
		"vehicle_configuration": vehicle_configuration,
		"status": "unknown",
		"fits": None,
		"message": _("No fitment data for this part."),
	}


@frappe.whitelist()
def validate_item_fitment(
	item: str,
	vehicle_configuration: str | None = None,
	vehicle_garage: str | None = None,
) -> dict:
	if not item:
		frappe.throw(_("Item is required."))

	if not vehicle_configuration and vehicle_garage:
		vehicle_configuration = resolve_vehicle_configuration_from_garage(vehicle_garage)

	return check_item_fitment(item, vehicle_configuration)


@frappe.whitelist()
def validate_sales_order_fitment(
	vehicle_garage: str | None = None,
	vehicle_configuration: str | None = None,
	items: list | str | None = None,
) -> list[dict]:
	if isinstance(items, str):
		items = json.loads(items)

	if not vehicle_configuration and vehicle_garage:
		vehicle_configuration = resolve_vehicle_configuration_from_garage(vehicle_garage)

	if not vehicle_configuration:
		return []

	seen = set()
	results = []
	for item in items or []:
		item_code = (item or "").strip()
		if not item_code or item_code in seen:
			continue
		seen.add(item_code)
		results.append(check_item_fitment(item_code, vehicle_configuration))

	return results
