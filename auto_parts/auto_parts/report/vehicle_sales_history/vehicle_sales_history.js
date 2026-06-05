// Copyright (c) 2026, Masood Javid and contributors

frappe.query_reports["Vehicle Sales History"] = {
	filters: [
		{
			fieldname: "vehicle_garage",
			label: __("Vehicle Garage"),
			fieldtype: "Link",
			options: "Vehicle Garage",
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
		},
	],
};
