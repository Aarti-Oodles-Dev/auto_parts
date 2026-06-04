import frappe


def after_install():
	"""Post-install setup for Auto Parts app."""
	frappe.clear_cache()
	create_auto_parts_settings()
	create_default_marketplace_channels()


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
