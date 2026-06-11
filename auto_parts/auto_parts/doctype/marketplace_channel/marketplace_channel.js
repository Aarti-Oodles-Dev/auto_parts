// Copyright (c) 2026, Masood Javid and contributors

frappe.ui.form.on("Marketplace Channel", {
	refresh(frm) {
		if (frm.is_new()) {
			frm.set_intro(
				__(
					"Create one document per marketplace (eBay, Amazon, Shopify). Add API credentials when the client provides them."
				)
			);
			return;
		}

		frm.add_custom_button(__("Test Connection"), () => {
			frappe.call({
				method:
					"auto_parts.auto_parts.doctype.marketplace_channel.marketplace_channel.test_connection",
				args: { channel_name: frm.doc.channel_name },
				freeze: true,
				freeze_message: __("Testing connection..."),
				callback(r) {
					const ok = r.message?.success;
					frappe.msgprint({
						title: ok ? __("Connection OK") : __("Connection Failed"),
						message: r.message?.message || __("No response."),
						indicator: ok ? "green" : "red",
					});
				},
			});
		});
	},
});
