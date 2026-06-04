// Copyright (c) 2026, Masood Javid and contributors
// For license information, please see license.txt

frappe.ui.form.on("Marketplace Channel", {
	refresh(frm) {
		if (frm.is_new()) {
			frm.set_intro(__("Create one document per marketplace (eBay, Amazon, Shopify)."));
		}
	},
});
