// Copyright (c) 2026, Masood Javid and contributors

function get_linked_sales_order(frm) {
	const orders = new Set();
	(frm.doc.items || []).forEach((row) => {
		if (row.sales_order) {
			orders.add(row.sales_order);
		}
	});
	return orders.size ? [...orders][0] : null;
}

function copy_vehicle_from_linked_so(frm) {
	if (frm.doc.vehicle_garage) {
		return;
	}

	const sales_order = get_linked_sales_order(frm);
	if (!sales_order) {
		return;
	}

	frappe.db.get_value("Sales Order", sales_order, ["vehicle_garage", "vin"]).then((r) => {
		if (r.message?.vehicle_garage) {
			frm.set_value("vehicle_garage", r.message.vehicle_garage);
			frm.set_value("vin", r.message.vin || "");
		}
	});
}

frappe.ui.form.on("Sales Invoice", {
	onload(frm) {
		frm.set_query("vehicle_garage", () => {
			if (!frm.doc.customer) {
				return { filters: { name: ["in", []] } };
			}
			return {
				filters: {
					customer: frm.doc.customer,
					is_active: 1,
				},
			};
		});
	},

	refresh(frm) {
		copy_vehicle_from_linked_so(frm);
	},

	items_add(frm) {
		copy_vehicle_from_linked_so(frm);
	},

	customer(frm) {
		if (frm.doc.vehicle_garage) {
			frappe.db.get_value("Vehicle Garage", frm.doc.vehicle_garage, "customer").then((r) => {
				if (r.message?.customer && r.message.customer !== frm.doc.customer) {
					frm.set_value("vehicle_garage", "");
					frm.set_value("vin", "");
				}
			});
		}
	},

	vehicle_garage(frm) {
		if (!frm.doc.vehicle_garage) {
			frm.set_value("vin", "");
			return;
		}
		frappe.db.get_value("Vehicle Garage", frm.doc.vehicle_garage, "vin").then((r) => {
			frm.set_value("vin", r.message?.vin || "");
		});
	},
});
