// Copyright (c) 2026, Masood Javid and contributors

frappe.ui.form.on("Part Fitment", {
	onload(frm) {
		if (frm.is_new()) {
			if (frappe.route_options?.item && !frm.doc.item) {
				frm.set_value("item", frappe.route_options.item);
			}
			if (frappe.route_options?.vehicle_configuration && !frm.doc.vehicle_configuration) {
				frm.set_value("vehicle_configuration", frappe.route_options.vehicle_configuration);
			}
			if (!frm.doc.source) {
				frm.set_value("source", "Manual");
			}
		}
	},

	vehicle_configuration(frm) {
		if (!frm.doc.vehicle_configuration) {
			frm.set_intro("");
			return;
		}
		frappe.db.get_doc("Vehicle Configuration", frm.doc.vehicle_configuration).then((doc) => {
			frm.set_intro(
				__("{0} {1} {2}", [doc.year || "", doc.make || "", doc.model || ""]).trim(),
				"blue"
			);
		});
	},
});
