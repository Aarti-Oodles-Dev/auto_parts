// Copyright (c) 2026, Masood Javid and contributors

frappe.ui.form.on("Auto Parts Settings", {
	refresh(frm) {
		frm.set_intro(
			__(
				"VIN: leave API URL empty to use free NHTSA decode. Marketplace: enable sync, configure channels, then use the buttons below."
			)
		);

		frm.add_custom_button(__("Marketplace Channels"), () => {
			frappe.set_route("List", "Marketplace Channel");
		});

		frm.add_custom_button(__("Marketplace Listings"), () => {
			frappe.set_route("List", "Marketplace Listing");
		});

		if (frm.doc.enable_marketplace_sync) {
			frm.add_custom_button(__("Sync All Listings"), () => {
				frappe.call({
					method: "auto_parts.marketplace.sync_engine.trigger_sync_all",
					freeze: true,
					freeze_message: __("Queuing marketplace stock sync..."),
					callback() {
						frappe.show_alert({
							message: __("Stock sync queued."),
							indicator: "green",
						});
					},
				});
			}, __("Marketplace"));

			frm.add_custom_button(__("Import Orders"), () => {
				frappe.call({
					method: "auto_parts.marketplace.sync_engine.trigger_import_orders",
					freeze: true,
					freeze_message: __("Queuing marketplace order import..."),
					callback() {
						frappe.show_alert({
							message: __("Order import queued."),
							indicator: "green",
						});
					},
				});
			}, __("Marketplace"));
		}
	},
});
