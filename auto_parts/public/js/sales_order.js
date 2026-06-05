// Copyright (c) 2026, Masood Javid and contributors

frappe.ui.form.on("Sales Order", {
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
		frm.trigger("toggle_vin_editability");
		frm.trigger("toggle_auto_parts_flags");
		frm.trigger("setup_auto_parts_buttons");
	},

	toggle_vin_editability(frm) {
		// Garage empty --> type/paste VIN . Garage set -->VIN from garage.
		frm.set_df_property("vin", "read_only", frm.doc.vehicle_garage ? 1 : 0);
	},

	customer(frm) {
		frm.set_value("vehicle_garage", "");
		frm.set_value("vin", "");
		frm.trigger("apply_customer_commercial_defaults");
	},

	vehicle_garage(frm) {
		frm.trigger("toggle_vin_editability");
		if (!frm.doc.vehicle_garage) {
			frm.set_value("vin", "");
			return;
		}
		frappe.db.get_value("Vehicle Garage", frm.doc.vehicle_garage, "vin").then((r) => {
			frm._vin_from_garage = true;
			frm.set_value("vin", r.message?.vin || "");
		});
	},

	vin(frm) {
		if (frm._vin_from_garage) {
			frm._vin_from_garage = false;
			return;
		}

		const vin = (frm.doc.vin || "").trim().toUpperCase();
		if (vin.length !== 17) {
			return;
		}

		if (!frm.doc.customer) {
			frappe.msgprint(__("Select Customer before decoding VIN."));
			return;
		}

		frappe.call({
			method: "auto_parts.vin.decode.apply_vin_to_sales_order",
			args: { vin, customer: frm.doc.customer },
			freeze: true,
			freeze_message: __("Looking up VIN..."),
			callback(r) {
				if (!r.message) return;

				if (r.message.vehicle_garage) {
					frm._vin_from_garage = true;
					frm.set_value("vehicle_garage", r.message.vehicle_garage);
					frappe.show_alert({
						message: __("Vehicle Garage linked from VIN."),
						indicator: "green",
					});
					return;
				}

				frappe.show_alert({
					message: __("VIN decoded: {0} {1} {2}. Create a Vehicle Garage to save this vehicle.", [
						r.message.year || "",
						r.message.make || "",
						r.message.model || "",
					]),
					indicator: "orange",
				});
			},
		});
	},

	is_special_order(frm) {
		if (frm.doc.is_special_order && frm.doc.is_buyout) {
			frm.set_value("is_buyout", 0);
		}
		frm.trigger("toggle_auto_parts_flags");
	},

	is_buyout(frm) {
		if (frm.doc.is_buyout && frm.doc.is_special_order) {
			frm.set_value("is_special_order", 0);
		}
		frm.trigger("toggle_auto_parts_flags");
	},

	toggle_auto_parts_flags(frm) {
		frm.toggle_enable("is_buyout", !!frm.doc.customer);
	},

	apply_customer_commercial_defaults(frm) {
		if (!frm.doc.customer || frm.doc.__islocal) {
			return;
		}
		frappe.call({
			method: "auto_parts.sales.sales_order.get_customer_commercial_details",
			args: { customer: frm.doc.customer },
			callback(r) {
				if (!r.message) return;
				const { pricing_tier, allow_buyout, selling_price_list } = r.message;

				if (pricing_tier) {
					frm.set_intro(
						__("Customer tier: {0}", [pricing_tier]) +
							(allow_buyout ? " | " + __("Buyout allowed") : ""),
						"blue"
					);
				} else {
					frm.set_intro("");
				}

				if (selling_price_list) {
					frm.set_value("selling_price_list", selling_price_list);
				}

				if (!allow_buyout && frm.doc.is_buyout) {
					frm.set_value("is_buyout", 0);
				}
			},
		});
	},

	setup_auto_parts_buttons(frm) {
		if (frm.is_new()) {
			return;
		}

		if (!frm.is_new()) {
			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Purchase Order",
					filters: { linked_sales_order: frm.doc.name, docstatus: ["<", 2] },
					fields: ["name", "is_buyout_po"],
				},
				callback(r) {
					(r.message || []).forEach((po) => {
						const label = po.is_buyout_po
							? __("View Buyout PO: {0}", [po.name])
							: __("View Special Order PO: {0}", [po.name]);
						frm.add_custom_button(label, () => {
							frappe.set_route("Form", "Purchase Order", po.name);
						});
					});
				},
			});
		}

		if (frm.doc.docstatus !== 0) {
			return;
		}

		if (frm.doc.is_special_order) {
			frm.add_custom_button(__("Create Special Order PO"), () => {
				frm.events.create_linked_po(frm, "special");
			});
		}

		if (frm.doc.is_buyout) {
			frm.add_custom_button(__("Create Buyout PO"), () => {
				frm.events.create_linked_po(frm, "buyout");
			});
		}
	},

	create_linked_po(frm, po_type) {
		const method =
			po_type === "buyout"
				? "auto_parts.sales.sales_order.create_buyout_po"
				: "auto_parts.sales.sales_order.create_special_order_po";

		const save_first = () => {
			if (frm.is_dirty()) {
				return frm.save().then(() => prompt_supplier_and_create());
			}
			return prompt_supplier_and_create();
		};

		const prompt_supplier_and_create = () => {
			frappe.prompt(
				[
					{
						fieldname: "supplier",
						fieldtype: "Link",
						label: __("Supplier"),
						options: "Supplier",
						reqd: 1,
					},
				],
				(values) => {
					frappe.call({
						method,
						args: {
							sales_order: frm.doc.name,
							supplier: values.supplier,
						},
						freeze: true,
						freeze_message: __("Creating Purchase Order..."),
						callback(r) {
							if (r.message?.purchase_order) {
								frappe.set_route("Form", "Purchase Order", r.message.purchase_order);
							}
						},
					});
				},
				__(
					po_type === "buyout"
						? "Create Buyout Purchase Order"
						: "Create Special Order Purchase Order"
				),
				__("Create")
			);
		};

		save_first();
	},
});
