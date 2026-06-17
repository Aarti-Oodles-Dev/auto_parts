import frappe


def after_install():
	"""Post-install setup for Auto Parts app."""
	frappe.clear_cache()
	create_auto_parts_settings()
	create_default_marketplace_channels()
	create_default_price_lists()
	create_default_pos_profile()
	enable_barcode_scanning()


def create_auto_parts_settings():
	if frappe.db.exists("Auto Parts Settings", "Auto Parts Settings"):
		return

	doc = frappe.get_doc(
		{
			"doctype": "Auto Parts Settings",
			"default_vehicle_garage_naming": "VG-.YYYY.-.#####",
			"enable_vin_decode_cache": 1,
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()


def create_default_marketplace_channels():
	for channel_name in ("eBay", "Amazon", "Shopify"):
		if frappe.db.exists("Marketplace Channel", channel_name):
			continue
		frappe.get_doc(
			{
				"doctype": "Marketplace Channel",
				"channel_name": channel_name,
				"enabled": 0,
			}
		).insert(ignore_permissions=True)
	frappe.db.commit()


def create_default_price_lists():
	company = frappe.defaults.get_global_default("company")
	if not company:
		company = frappe.db.get_single_value("Global Defaults", "default_company")
	if not company:
		return

	currency = frappe.db.get_value("Company", company, "default_currency") or "INR"
	for price_list_name in ("Retail", "Commercial", "Marketplace"):
		if frappe.db.exists("Price List", price_list_name):
			continue
		frappe.get_doc(
			{
				"doctype": "Price List",
				"price_list_name": price_list_name,
				"currency": currency,
				"selling": 1,
				"buying": 0,
				"enabled": 1,
			}
		).insert(ignore_permissions=True)
	frappe.db.commit()


def create_default_pos_profile():
	"""Draft POS profile for counter sales (row 84). Skips if mandatory company accounts missing."""
	company = frappe.defaults.get_global_default("company")
	if not company:
		company = frappe.db.get_single_value("Global Defaults", "default_company")
	if not company or frappe.db.exists("POS Profile", "Auto Parts Counter"):
		return

	warehouse = frappe.db.get_value(
		"Warehouse", {"company": company, "is_group": 0}, "name", order_by="creation asc"
	)
	if not warehouse or not frappe.db.exists("Price List", "Retail"):
		return

	write_off_account = frappe.db.get_value("Company", company, "default_expense_account")
	write_off_cost_center = frappe.db.get_value("Company", company, "cost_center")
	if not write_off_account or not write_off_cost_center:
		return

	try:
		frappe.get_doc(
			{
				"doctype": "POS Profile",
				"name": "Auto Parts Counter",
				"company": company,
				"warehouse": warehouse,
				"selling_price_list": "Retail",
				"currency": frappe.db.get_value("Company", company, "default_currency"),
				"write_off_account": write_off_account,
				"write_off_cost_center": write_off_cost_center,
				"update_stock": 1,
				"allow_print_before_pay": 1,
			}
		).insert(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.log_error(title="Auto Parts POS Profile setup skipped")


def enable_barcode_scanning():
	"""Enable ERPNext core barcode fields for warehouse mobile workflows."""
	frappe.db.set_single_value("Stock Settings", "show_barcode_field", 1)
	frappe.db.commit()
