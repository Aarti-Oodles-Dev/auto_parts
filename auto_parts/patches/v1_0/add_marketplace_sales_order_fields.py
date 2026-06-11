# Copyright (c) 2026, Masood Javid and contributors

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	fields = {
		"Sales Order": [
			{
				"fieldname": "marketplace_order_id",
				"fieldtype": "Data",
				"label": "Marketplace Order ID",
				"insert_after": "is_buyout",
				"read_only": 1,
				"unique": 1,
				"allow_on_submit": 1,
			},
			{
				"fieldname": "marketplace_channel",
				"fieldtype": "Link",
				"label": "Marketplace Channel",
				"options": "Marketplace Channel",
				"insert_after": "marketplace_order_id",
				"read_only": 1,
				"allow_on_submit": 1,
			},
		]
	}
	create_custom_fields(fields, update=True)
