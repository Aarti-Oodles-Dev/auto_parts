import frappe


def execute():
	frappe.db.set_single_value("Stock Settings", "show_barcode_field", 1)
