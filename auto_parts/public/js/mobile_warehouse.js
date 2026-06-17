// Copyright (c) 2026, Masood Javid and contributors

const MOBILE_WAREHOUSE_DOCTYPES = ["Pick List", "Stock Entry", "Purchase Receipt"];

function is_mobile_view() {
	return window.innerWidth <= 768;
}

function setup_mobile_warehouse(frm) {
	if (!is_mobile_view()) {
		$(document.body).removeClass("auto-parts-mobile-warehouse");
		return;
	}

	$(document.body).addClass("auto-parts-mobile-warehouse");

	if (!frm.fields_dict.scan_barcode) {
		return;
	}

	frm.toggle_display("scan_barcode", true);
	setTimeout(() => {
		frm.fields_dict.scan_barcode?.$input?.focus();
	}, 300);
}

for (const doctype of MOBILE_WAREHOUSE_DOCTYPES) {
	frappe.ui.form.on(doctype, {
		onload(frm) {
			setup_mobile_warehouse(frm);
		},
		refresh(frm) {
			setup_mobile_warehouse(frm);
		},
	});
}
