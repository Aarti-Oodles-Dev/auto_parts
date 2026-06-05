# Copyright (c) 2026, Masood Javid and contributors

from frappe import _


def get_dashboard_data(data):
	for group in data.transactions:
		if group.get("label") == _("Fitment") and "Part Fitment" in group.get("items", []):
			return data

	data.transactions.append({"label": _("Fitment"), "items": ["Part Fitment"]})
	data.setdefault("non_standard_fieldnames", {})
	data.non_standard_fieldnames["Part Fitment"] = "item"
	return data
