# Copyright (c) 2026, Masood Javid and contributors

"""Lists failed, skipped, and pending ACES-PIES staging lines so they can be corrected."""

import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{
			"label": _("Import Batch"),
			"fieldname": "parent",
			"fieldtype": "Link",
			"options": "ACES PIES Import Batch",
			"width": 160,
		},
		{"label": _("Type"), "fieldname": "import_type", "fieldtype": "Data", "width": 80},
		{"label": _("Raw SKU"), "fieldname": "raw_sku", "fieldtype": "Data", "width": 150},
		{"label": _("Status"), "fieldname": "import_status", "fieldtype": "Data", "width": 100},
		{
			"label": _("Target Item"),
			"fieldname": "target_item",
			"fieldtype": "Link",
			"options": "Item",
			"width": 150,
		},
		{
			"label": _("Error Message"),
			"fieldname": "error_message",
			"fieldtype": "Small Text",
			"width": 320,
		},
	]


def get_data(filters):
	conditions = ["line.parenttype = 'ACES PIES Import Batch'"]
	values = {}

	status = filters.get("import_status")
	if status:
		conditions.append("line.import_status = %(import_status)s")
		values["import_status"] = status
	else:
		conditions.append("line.import_status in ('Failed', 'Skipped', 'Pending')")

	if filters.get("import_batch"):
		conditions.append("line.parent = %(import_batch)s")
		values["import_batch"] = filters["import_batch"]

	if filters.get("import_type"):
		conditions.append("batch.import_type = %(import_type)s")
		values["import_type"] = filters["import_type"]

	where_clause = " and ".join(conditions)

	return frappe.db.sql(
		f"""
		select
			line.parent,
			batch.import_type,
			line.raw_sku,
			line.import_status,
			line.target_item,
			line.error_message
		from `tabACES PIES Import Line` line
		inner join `tabACES PIES Import Batch` batch on batch.name = line.parent
		where {where_clause}
		order by line.parent desc, line.idx asc
		""",
		values,
		as_dict=True,
	)
