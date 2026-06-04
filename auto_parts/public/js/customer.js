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

frappe.ui.form.on("Customer", {
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
	},

	pricing_tier(frm) {
		if (!frm.doc.pricing_tier) {
			return;
		}
		apply_tier_price_list(frm);
	},
});
