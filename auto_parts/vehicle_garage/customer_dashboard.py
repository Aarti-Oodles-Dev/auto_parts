# Copyright (c) 2026, Masood Javid and contributors

from frappe import _


def get_dashboard_data(data):

	for group in data.transactions:
		if group.get("label") == _("Vehicles") and "Vehicle Garage" in group.get("items", []):
			return data

	data.transactions.append({"label": _("Vehicles"), "items": ["Vehicle Garage"]})
	return data
