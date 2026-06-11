// Copyright (c) 2026, Masood Javid and contributors

let reference_import_poll_timer = null;

frappe.ui.form.on("Catalog Reference Import Batch", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}

		if (frm.doc.status !== "Processing") {
			frm.add_custom_button(__("Import File"), () => enqueue_reference_import(frm)).addClass(
				"btn-primary"
			);
		}

		if (!frm.doc.import_file) {
			frm.dashboard.set_headline(
				__(
					"Attach a CSV file, then click <b>Import File</b>. Required columns depend on the reference type."
				)
			);
		}

		if (frm.doc.status === "Processing") {
			frm.dashboard.set_headline(__("Import running in background..."));
			start_reference_import_poll(frm);
		} else {
			stop_reference_import_poll();
		}
	},

	onload(frm) {
		if (frm.doc.status === "Processing") {
			start_reference_import_poll(frm);
		}
	},
});

function enqueue_reference_import(frm) {
	frm.reload_doc().then(() => {
		if (!frm.doc.import_file) {
			frappe.msgprint({
				title: __("No file attached"),
				message: __("Attach a CSV file before importing."),
				indicator: "orange",
			});
			return;
		}

		frappe.call({
			method:
				"auto_parts.auto_parts.doctype.catalog_reference_import_batch.catalog_reference_import_batch.enqueue_import",
			args: { batch_name: frm.doc.name },
			freeze: true,
			freeze_message: __("Queuing reference import..."),
			callback() {
				frm.reload_doc().then(() => start_reference_import_poll(frm));
			},
		});
	});
}

function start_reference_import_poll(frm) {
	stop_reference_import_poll();
	reference_import_poll_timer = setInterval(() => poll_reference_import_status(frm), 3000);
}

function stop_reference_import_poll() {
	if (reference_import_poll_timer) {
		clearInterval(reference_import_poll_timer);
		reference_import_poll_timer = null;
	}
}

function poll_reference_import_status(frm) {
	frappe.call({
		method:
			"auto_parts.auto_parts.doctype.catalog_reference_import_batch.catalog_reference_import_batch.get_batch_status",
		args: { batch_name: frm.doc.name },
		callback(r) {
			const status = r.message?.status;
			if (!status || status === "Processing") {
				return;
			}

			stop_reference_import_poll();
			frm.reload_doc().then(() => {
				if (status === "Completed") {
					frappe.show_alert({
						message: __("Imported {0} rows.", [r.message.imported_rows || 0]),
						indicator: "green",
					});
				} else if (status === "Failed") {
					frappe.msgprint({
						title: __("Import Failed"),
						message: __("Check import lines and the Error Log for details."),
						indicator: "red",
					});
				}
			});
		},
	});
}
