# Copyright (c) 2026, Masood Javid and contributors

from frappe import _


def get_data():
	return {
		"fieldname": "vehicle_garage",
		"transactions": [{"label": _("Sales"), "items": ["Sales Order", "Sales Invoice"]}],
	}
