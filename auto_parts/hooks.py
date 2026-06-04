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
    {"dt": "Workflow", "filters": [["name", "=", "Transfer Approval"]]},
    {"dt": "Workflow State", "filters": [["name", "in", ["Draft", "Pending Approval", "Approved", "Rejected"]]]},
    {"dt": "Workflow Action Master", "filters": [["name", "in", ["Pending Approval"]]]},
]

# Daily auto-run ke liye
scheduler_events = {
    "daily": [
        "auto_parts.auto_parts.doctype.auto_parts_settings.auto_parts_settings.create_reorder_material_requests"
    ]
}