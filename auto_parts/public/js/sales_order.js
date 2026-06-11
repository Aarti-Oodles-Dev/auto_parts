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
		frm.trigger("setup_fitment_validation");
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
			frm.trigger("clear_fitment_validation");
			return;
		}
		frappe.db.get_value("Vehicle Garage", frm.doc.vehicle_garage, "vin").then((r) => {
			frm._vin_from_garage = true;
			frm.set_value("vin", r.message?.vin || "");
		});
		frm.trigger("validate_so_fitment");
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

	setup_fitment_validation(frm) {
		frm._fitment_mismatches = frm._fitment_mismatches || [];
		frm.trigger("clear_fitment_validation");

		if (frm.doc.docstatus !== 0 || !frm.doc.vehicle_garage) {
			return;
		}

		frm.add_custom_button(
			__("Find Parts for Vehicle"),
			() => show_vehicle_parts_dialog(frm),
			__("Auto Parts")
		);

		if ((frm.doc.items || []).some((row) => row.item_code)) {
			frm.trigger("validate_so_fitment");
		} else if ((frm._fitment_mismatches || []).length) {
			frm.trigger("show_fitment_warnings");
		}
	},

	clear_fitment_validation(frm) {
		frm._fitment_mismatches = [];
		if (frm._fitment_comment) {
			frm.dashboard.remove_comment(frm._fitment_comment);
			frm._fitment_comment = null;
		}
		frm.remove_custom_button(__("View Alternates"), __("Auto Parts"));
	},

	validate_so_fitment(frm) {
		if (frm.doc.docstatus !== 0 || !frm.doc.vehicle_garage) {
			return;
		}

		const item_codes = (frm.doc.items || []).map((row) => row.item_code).filter(Boolean);
		if (!item_codes.length) {
			frm.trigger("clear_fitment_validation");
			return;
		}

		frappe.call({
			method: "auto_parts.fitment.validation.validate_sales_order_fitment",
			args: {
				vehicle_garage: frm.doc.vehicle_garage,
				items: item_codes,
			},
			callback(r) {
				const mismatches = (r.message || []).filter((row) => row.status === "mismatch");
				frm._fitment_mismatches = mismatches;
				frm.trigger("show_fitment_warnings");
			},
		});
	},

	show_fitment_warnings(frm) {
		if (frm._fitment_comment) {
			frm.dashboard.remove_comment(frm._fitment_comment);
			frm._fitment_comment = null;
		}
		frm.remove_custom_button(__("View Alternates"), __("Auto Parts"));

		const mismatches = frm._fitment_mismatches || [];
		if (!mismatches.length) {
			return;
		}

		const items = mismatches.map((row) => frappe.utils.escape_html(row.item)).join(", ");
		frm._fitment_comment = frm.dashboard.add_comment(
			__(
				"Fitment warning: {0} may not fit the selected vehicle. Use <b>View Alternates</b> in Auto Parts.",
				[items]
			),
			"orange",
			true
		);

		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("View Alternates"), () => show_alternates_dialog(frm), __("Auto Parts"));
		}
	},
});

frappe.ui.form.on("Sales Order Item", {
	item_code(frm) {
		frm.trigger("validate_so_fitment");
	},

	items_remove(frm) {
		frm.trigger("validate_so_fitment");
	},
});

function show_vehicle_parts_dialog(frm) {
	frappe.call({
		method: "auto_parts.fitment.search.search_parts_by_vehicle",
		args: { vehicle_garage: frm.doc.vehicle_garage },
		freeze: true,
		freeze_message: __("Loading parts for vehicle..."),
		callback(r) {
			const rows = r.message || [];
			if (!rows.length) {
				frappe.msgprint(__("No parts found for this vehicle."));
				return;
			}

			const dialog = new frappe.ui.Dialog({
				title: __("Parts for Vehicle"),
				size: "large",
				fields: [
					{
						fieldtype: "HTML",
						fieldname: "results",
					},
				],
			});

			const html = rows
				.map(
					(row) =>
						`<tr>
							<td><a href="#" data-item="${frappe.utils.escape_html(row.item)}">${frappe.utils.escape_html(row.item)}</a></td>
							<td>${frappe.utils.escape_html(row.item_name || "")}</td>
							<td>${frappe.utils.escape_html(row.position || "")}</td>
							<td>${row.qty || 1}</td>
						</tr>`
				)
				.join("");

			dialog.fields_dict.results.$wrapper.html(`
				<table class="table table-bordered table-sm">
					<thead>
						<tr>
							<th>${__("Item")}</th>
							<th>${__("Name")}</th>
							<th>${__("Position")}</th>
							<th>${__("Qty")}</th>
						</tr>
					</thead>
					<tbody>${html}</tbody>
				</table>
			`);

			dialog.fields_dict.results.$wrapper.find("a[data-item]").on("click", (e) => {
				e.preventDefault();
				const item_code = e.currentTarget.getAttribute("data-item");
				dialog.hide();
				add_item_to_sales_order(frm, item_code);
			});

			dialog.show();
		},
	});
}

function show_alternates_dialog(frm) {
	const mismatches = frm._fitment_mismatches || [];
	if (!mismatches.length) {
		frappe.msgprint(__("No fitment mismatches on this order."));
		return;
	}

	const item = mismatches[0].item;
	frappe.call({
		method: "auto_parts.fitment.alternates.get_smart_alternates",
		args: {
			item,
			vehicle_configuration: mismatches[0].vehicle_configuration,
		},
		freeze: true,
		freeze_message: __("Loading alternates..."),
		callback(r) {
			const data = r.message || {};
			const supersession = (data.supersession_chain || []).join(" → ");
			const alternates = data.fitment_alternates || [];

			let message = `<p><b>${frappe.utils.escape_html(item)}</b></p>`;
			if (supersession) {
				message += `<p>${__("Supersession")}: ${frappe.utils.escape_html(supersession)}</p>`;
			}

			if (!alternates.length) {
				message += `<p>${__("No alternate parts found for this vehicle.")}</p>`;
				frappe.msgprint({ title: __("Smart Alternates"), message });
				return;
			}

			message += `<table class="table table-bordered table-sm"><thead><tr>
				<th>${__("Item")}</th><th>${__("Name")}</th><th>${__("Position")}</th>
			</tr></thead><tbody>`;
			alternates.forEach((row) => {
				message += `<tr>
					<td><a href="#" class="alt-item" data-item="${frappe.utils.escape_html(row.item)}">${frappe.utils.escape_html(row.item)}</a></td>
					<td>${frappe.utils.escape_html(row.item_name || "")}</td>
					<td>${frappe.utils.escape_html(row.position || "")}</td>
				</tr>`;
			});
			message += "</tbody></table>";

			const d = frappe.msgprint({
				title: __("Smart Alternates"),
				message,
				wide: true,
			});

			d.$wrapper.find("a.alt-item").on("click", (e) => {
				e.preventDefault();
				frappe.hide_msgprint();
				add_item_to_sales_order(frm, e.currentTarget.getAttribute("data-item"));
			});
		},
	});
}

function add_item_to_sales_order(frm, item_code) {
	const exists = (frm.doc.items || []).some((row) => row.item_code === item_code);
	if (exists) {
		frappe.show_alert({ message: __("Item already on this order."), indicator: "orange" });
		return;
	}

	const row = frm.add_child("items");
	frappe.model.set_value(row.doctype, row.name, "item_code", item_code);
	frm.refresh_field("items");
	frm.trigger("validate_so_fitment");
}
