// Copyright (c) 2026, Masood Javid and contributors

function apply_decoded_to_garage(frm, data) {
	const updates = {
		year: data.year,
		make: data.make,
		model: data.model,
		engine: data.engine,
	};
	if (data.vehicle_configuration) {
		updates.vehicle_configuration = data.vehicle_configuration;
	}
	frm.set_value(updates);

	const source = data.from_cache ? __("cache") : __("API");
	frappe.show_alert({
		message: __("VIN decoded from {0}: {1} {2} {3}", [
			source,
			data.year || "",
			data.make || "",
			data.model || "",
		]),
		indicator: "green",
	});
}

frappe.ui.form.on("Vehicle Garage", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.naming_series) {
			frappe.db
				.get_single_value("Auto Parts Settings", "default_vehicle_garage_naming")
				.then((series) => {
					if (series) {
						frm.set_value("naming_series", series);
					}
				});
		}

		if (frm.is_new() && frappe.route_options?.customer && !frm.doc.customer) {
			frm.set_value("customer", frappe.route_options.customer);
		}
	},

	refresh(frm) {
		frm.add_custom_button(__("Decode VIN"), () => frm.events.decode_vin(frm));

		if (!frm.is_new()) {
			frm.add_custom_button(__("Sales History"), () => {
				frappe.set_route("query-report", "Vehicle Sales History", {
					vehicle_garage: frm.doc.name,
					customer: frm.doc.customer,
				});
			});
		}
	},

	decode_vin(frm) {
		const vin = (frm.doc.vin || "").trim();
		if (vin.length !== 17) {
			frappe.msgprint(__("Enter a valid 17-character VIN before decoding."));
			return;
		}

		frappe.call({
			method: "auto_parts.vin.decode.decode_vin",
			args: { vin },
			freeze: true,
			freeze_message: __("Decoding VIN..."),
			callback(r) {
				if (r.message) {
					apply_decoded_to_garage(frm, r.message);
				}
			},
		});
	},

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
