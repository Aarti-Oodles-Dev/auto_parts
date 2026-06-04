app_name = "auto_parts"
app_title = "Auto Parts"
app_publisher = "Masood Javid"
app_description = "Auto Parts Inventory ERP for automotive multi-store businesses"
app_email = "yogendra@masoodjavid.com"
app_license = "mit"

required_apps = ["erpnext"]

add_to_apps_screen = [
	{
		"name": "auto_parts",
		"logo": "/assets/auto_parts/logo.png",
		"title": "Auto Parts",
		"route": "/app/auto-parts-settings",
		"has_permission": "auto_parts.api.permission.has_app_permission",
	}
]

after_install = "auto_parts.install.after_install"

doctype_js = {
	"Sales Order": "public/js/sales_order.js",
	"Sales Invoice": "public/js/sales_invoice.js",
	"Customer": "public/js/customer.js",
}

doc_events = {
	"Sales Order": {
		"validate": "auto_parts.sales.sales_order.validate_sales_order",
		"on_submit": "auto_parts.sales.sales_order.on_submit_sales_order",
	},
	"Sales Invoice": {
		"before_insert": "auto_parts.sales.sales_order.copy_vehicle_from_sales_order",
		"validate": "auto_parts.sales.sales_order.validate_sales_invoice_garage",
	},
	"Purchase Order": {
		"validate": "auto_parts.sales.purchase_order.validate_purchase_order",
	},
	"Customer": {
		"validate": "auto_parts.sales.customer.validate_customer",
	},
}

fixtures = [
	{
		"dt": "Custom Field",
		"filters": [["module", "=", "Auto Parts"]],
	},
	{
		"dt": "DocType",
		"filters": [["module", "=", "Auto Parts"]],
	},
]
