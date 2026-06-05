// Copyright (c) 2026, Masood Javid and contributors

const TIER_PRICE_LIST_MAP = {
	Retail: "Retail",
	Commercial: "Commercial",
	Fleet: "Commercial",
};

function apply_tier_price_list(frm) {
	const price_list = TIER_PRICE_LIST_MAP[frm.doc.pricing_tier];
	if (price_list) {
		frm.set_value("default_price_list", price_list);
	}
}

function ensure_vehicle_garage_dashboard(frm) {
	const transactions = frm.meta.__dashboard?.transactions || [];
	const has_vehicle_garage = transactions.some((group) =>
		(group.items || []).includes("Vehicle Garage")
	);

	if (!has_vehicle_garage) {
		frm.dashboard.add_transactions({
			label: __("Vehicles"),
			items: ["Vehicle Garage"],
		});
	}
}

frappe.ui.form.on("Customer", {
	onload(frm) {
		ensure_vehicle_garage_dashboard(frm);
	},

	refresh(frm) {
		if (frm.doc.pricing_tier) {
			frm.set_intro(
				__(
					"Pricing tier: {0}. Default Price List updates when you change the tier.",
					[frm.doc.pricing_tier]
				),
				"blue"
			);
		}

		if (!frm.is_new()) {
			frm.add_custom_button(
				__("New Vehicle"),
				() => {
					frappe.new_doc("Vehicle Garage", { customer: frm.doc.name });
				},
				__("Auto Parts")
			);

			frm.add_custom_button(
				__("View Vehicles"),
				() => {
					frappe.set_route("List", "Vehicle Garage", { customer: frm.doc.name });
				},
				__("Auto Parts")
			);
		}
	},

	pricing_tier(frm) {
		if (!frm.doc.pricing_tier) {
			return;
		}
		apply_tier_price_list(frm);
	},
});
