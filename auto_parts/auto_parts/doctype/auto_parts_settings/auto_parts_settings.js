// Copyright (c) 2026, Masood Javid and contributors
// For license information, please see license.txt

frappe.ui.form.on("Auto Parts Settings", {
	refresh(frm) {
		frm.set_intro(
			__(
				"VIN: leave API URL empty to use free NHTSA decode. Add URL/key for a commercial provider. Marketplace channels open from the button below."
			)
		);

		frm.add_custom_button(__("Marketplace Channels"), () => {
			frappe.set_route("List", "Marketplace Channel");
		});
	},
});
