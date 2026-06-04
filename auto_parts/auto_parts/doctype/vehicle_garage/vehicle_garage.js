// Copyright (c) 2026, Masood Javid and contributors
// For license information, please see license.txt

frappe.ui.form.on("Vehicle Garage", {
	vehicle_configuration(frm) {
		if (!frm.doc.vehicle_configuration) return;
		frappe.db.get_doc("Vehicle Configuration", frm.doc.vehicle_configuration).then((doc) => {
			frm.set_value({
				year: doc.year,
				make: doc.make,
				model: doc.model,
				engine: doc.engine,
			});
		});
	},
});
