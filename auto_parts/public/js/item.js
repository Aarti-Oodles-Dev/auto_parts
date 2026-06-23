// Copyright (c) 2026, Masood Javid and contributors

function ensure_part_fitment_dashboard(frm) {
	const transactions = frm.meta.__dashboard?.transactions || [];
	const has_fitment = transactions.some((group) =>
		(group.items || []).includes("Part Fitment")
	);

	if (!has_fitment) {
		frm.dashboard.add_transactions({
			label: __("Fitment"),
			items: ["Part Fitment"],
		});
	}
}

frappe.ui.form.on("Item", {
	onload(frm) {
		ensure_part_fitment_dashboard(frm);
	},

	refresh(frm) {
		if (frm.is_new()) {
			return;
		}

		frm.add_custom_button(
			__("New Fitment"),
			() => {
				frappe.new_doc("Part Fitment", { item: frm.doc.name });
			},
			__("Auto Parts")
		);

		frm.add_custom_button(
			__("View Fitments"),
			() => {
				frappe.set_route("List", "Part Fitment", { item: frm.doc.name });
			},
			__("Auto Parts")
		);

		frm.add_custom_button(
			__("Lookup Cross Reference"),
			() => {
				const dialog = new frappe.ui.Dialog({
					title: __("Lookup Cross Reference"),
					fields: [
						{
							fieldname: "lookup_part_number",
							label: __("Part Number"),
							fieldtype: "Data",
							reqd: 1,
						},
						{
							fieldname: "lookup_reference_type",
							label: __("Reference Type"),
							fieldtype: "Select",
							options: "\nOEM\nAftermarket\nInterchange\nCompetitor",
						},
						{
							fieldname: "lookup_brand_name",
							label: __("Brand"),
							fieldtype: "Data",
						},
					],
					primary_action_label: __("Search"),
					primary_action(values) {
						dialog.hide();
						frappe.call({
							method: "auto_parts.cross_reference.search.search_item_by_cross_reference",
							args: {
								part_number: values.lookup_part_number,
								reference_type: values.lookup_reference_type || null,
								brand_name: values.lookup_brand_name || null,
							},
							freeze: true,
							freeze_message: __("Searching..."),
							callback(r) {
								const rows = r.message || [];
								if (!rows.length) {
									frappe.msgprint(__("No item found for this cross reference."));
									return;
								}
								if (rows.length === 1) {
									const match = rows[0];
									if (match.item === frm.doc.name) {
										frappe.show_alert({
											message: __(
												"Cross reference {0} is on this item ({1}).",
												[match.part_number, match.item]
											),
											indicator: "green",
										});
										const tab = frm.wrapper.find(
											'.nav-link[data-fieldname="automotive_tab"]'
										);
										if (tab.length) {
											tab.trigger("click");
										}
										return;
									}
									frappe.show_alert({
										message: __("Opening item {0}", [match.item]),
										indicator: "green",
									});
									frappe.set_route("Form", "Item", match.item);
									return;
								}
								const message = rows
									.map(
										(row) =>
											`<a href="/app/item/${encodeURIComponent(row.item)}">${frappe.utils.escape_html(row.item)}</a> — ${frappe.utils.escape_html(row.item_name || "")} (${frappe.utils.escape_html(row.reference_type || "")})`
									)
									.join("<br>");
								frappe.msgprint({
									title: __("Matching Items"),
									message,
								});
							},
							error(r) {
								frappe.msgprint(
									r?.message || __("Cross reference search failed.")
								);
							},
						});
					},
				});
				dialog.show();
			},
			__("Auto Parts")
		);
		
            frm.add_custom_button(__('View Supersession Chain'), function() {
                frappe.call({
                    method: 'auto_parts.auto_parts.doctype.part_supersession.part_supersession.get_supersession_chain',
                    args: { item_code: frm.doc.name },
                    callback: function(r) {
                        if (r.message) {
                            let chain = r.message.join(' → ');
                            frappe.msgprint({
                                title: __('Supersession Chain'),
                                message: chain,
                                indicator: 'blue'
                            });
                        }
                    }
                });
            }, __('Auto Parts'));
        

        // Warning if this item is superseded
        if (frm.doc.superseded_by) {
            frm.dashboard.add_comment(
                `This part is superseded by <b>${frm.doc.superseded_by}</b>`,
                'orange', true
            );
        }
	},
	superseded_by: function(frm) {
        if (frm.doc.superseded_by && frm.doc.superseded_by === frm.doc.name) {
            frappe.throw(__('Item cannot supersede itself'));
        }
    }
});

frappe.ui.form.on("Item Cross Reference", {
	part_number(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.part_number) {
			return;
		}
		const normalized = row.part_number.trim().toUpperCase();
		if (normalized !== row.part_number) {
			frappe.model.set_value(cdt, cdn, "part_number", normalized);
		}
	},
});
