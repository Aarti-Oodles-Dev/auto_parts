// Copyright (c) 2026, Masood Javid and contributors

frappe.ui.form.on("Marketplace Listing", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}

		if (frm.doc.listing_status === "Active") {
			frm.add_custom_button(__("Sync Now"), () => sync_listing(frm), __("Marketplace"));
		}

		if (frm.doc.listing_status === "Draft") {
			frm.add_custom_button(
				__("Activate"),
				() => frm.set_value("listing_status", "Active"),
				__("Marketplace")
			);
		}

		if (frm.doc.listing_status === "Active") {
			frm.add_custom_button(
				__("Pause"),
				() => frm.set_value("listing_status", "Paused"),
				__("Marketplace")
			);
		}

		if (frm.doc.listing_status === "Paused") {
			frm.add_custom_button(
				__("Resume"),
				() => frm.set_value("listing_status", "Active"),
				__("Marketplace")
			);
		}

		frm.add_custom_button(__("Recalculate Price"), () => {
			frm.call("calculate_channel_price").then(() => {
				frm.refresh_field("listing_price");
			});
		}, __("Marketplace"));
	},

	pricing_method(frm) {
		frm.toggle_reqd("channel_markup_percent", frm.doc.pricing_method === "Cost Plus");
		frm.toggle_reqd("price_list", frm.doc.pricing_method === "Price List");
		frm.toggle_reqd("listing_price", frm.doc.pricing_method === "Fixed");
	},

	channel_markup_percent(frm) {
		if (frm.doc.pricing_method === "Cost Plus") {
			frm.call("calculate_channel_price").then(() => {
				frm.refresh_field("listing_price");
			});
		}
	},
});

function sync_listing(frm) {
	frappe.call({
		method: "auto_parts.marketplace.sync_engine.trigger_manual_sync",
		args: { listing: frm.doc.name },
		freeze: true,
		freeze_message: __("Syncing listing..."),
		callback(r) {
			const indicator = r.message?.success ? "green" : "orange";
			frappe.show_alert({
				message: r.message?.message || __("Sync completed."),
				indicator,
			});
			frm.reload_doc();
		},
	});
}
