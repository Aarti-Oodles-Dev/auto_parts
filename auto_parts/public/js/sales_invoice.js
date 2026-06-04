// Copyright (c) 2026, Masood Javid and contributors
// For license information, please see license.txt

frappe.ui.form.on("Sales Invoice", {
	vehicle_garage(frm) {
		if (!frm.doc.vehicle_garage) return;
		frappe.db.get_value("Vehicle Garage", frm.doc.vehicle_garage, "vin").then((r) => {
			frm.set_value("vin", r.message?.vin || "");
		});
	},
});
