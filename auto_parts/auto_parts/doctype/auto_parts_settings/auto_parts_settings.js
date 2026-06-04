// Copyright (c) 2026, Masood Javid and contributors
// For license information, please see license.txt

frappe.ui.form.on("Auto Parts Settings", {
	refresh(frm) {
		frm.set_intro(
			__(
				"Global defaults only. Open Marketplace Channel to configure eBay, Amazon, and Shopify."
			)
		);

		frm.add_custom_button(__("Marketplace Channels"), () => {
			frappe.set_route("List", "Marketplace Channel");
		});
	},
});
