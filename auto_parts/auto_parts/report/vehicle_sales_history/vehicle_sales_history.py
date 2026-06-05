# Copyright (c) 2026, Masood Javid and contributors

import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Sales Order"),
			"fieldname": "sales_order",
			"fieldtype": "Link",
			"options": "Sales Order",
			"width": 150,
		},
		{
			"label": _("Date"),
			"fieldname": "transaction_date",
			"fieldtype": "Date",
			"width": 100,
		},
		{
			"label": _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 150,
		},
		{
			"label": _("Vehicle Garage"),
			"fieldname": "vehicle_garage",
			"fieldtype": "Link",
			"options": "Vehicle Garage",
			"width": 150,
		},
		{"label": _("VIN"), "fieldname": "vin", "fieldtype": "Data", "width": 150},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 110},
		{
			"label": _("Grand Total"),
			"fieldname": "grand_total",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
	]


def get_data(filters):
	conditions = ["so.docstatus < 2", "IFNULL(so.vehicle_garage, '') != ''"]
	values = {}

	if filters.get("vehicle_garage"):
		conditions.append("so.vehicle_garage = %(vehicle_garage)s")
		values["vehicle_garage"] = filters["vehicle_garage"]

	if filters.get("customer"):
		conditions.append("so.customer = %(customer)s")
		values["customer"] = filters["customer"]

	if filters.get("company"):
		conditions.append("so.company = %(company)s")
		values["company"] = filters["company"]

	if filters.get("from_date"):
		conditions.append("so.transaction_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("so.transaction_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	where_clause = " and ".join(conditions)

	return frappe.db.sql(
		f"""
		select
			so.name as sales_order,
			so.transaction_date,
			so.customer,
			so.vehicle_garage,
			so.vin,
			so.status,
			so.grand_total,
			so.currency
		from `tabSales Order` so
		where {where_clause}
		order by so.transaction_date desc, so.name desc
		""",
		values,
		as_dict=True,
	)
