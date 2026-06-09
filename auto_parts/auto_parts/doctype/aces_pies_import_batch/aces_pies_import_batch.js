// Copyright (c) 2026, Masood Javid and contributors

frappe.ui.form.on("ACES PIES Import Batch", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}

		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Parse File"), () => parse_import_file(frm)).addClass(
				"btn-primary"
			);
		}

		if (!frm.doc.import_file && frm.doc.docstatus === 0) {
			frm.dashboard.set_headline(
				__(
					"Use <b>Import File → Attach</b> to upload your XML. When the file link appears, click <b>Parse File</b>."
				)
			);
		}

		if (frm.doc.status === "Processing") {
			frm.dashboard.set_headline(
				__("Processing... reload the page in a few seconds.")
			);
		}
	},

	import_file(frm) {
		if (frm.doc.import_file) {
			frappe.show_alert({
				message: __("File attached. Now click Parse File."),
				indicator: "green",
			});
		}
	},
});

function parse_import_file(frm) {
	// Reload first so Parse uses the saved import_file from the server.
	frm.reload_doc().then(() => {
		if (!frm.doc.import_file) {
			frappe.msgprint({
				title: __("No file attached"),
				message: __(
					"Use the <b>Import File</b> field:<br>1. Click <b>Attach</b><br>2. Choose your XML file<br>3. Click <b>Upload</b> in the popup<br>4. Wait until the file link appears<br>5. Then click <b>Parse File</b>"
				),
				indicator: "orange",
			});
			return;
		}

		frappe.call({
			method:
				"auto_parts.auto_parts.doctype.aces_pies_import_batch.aces_pies_import_batch.parse_import_file_now",
			args: { batch_name: frm.doc.name },
			freeze: true,
			freeze_message: __("Parsing XML file..."),
			callback(r) {
				if (r.message?.total_rows !== undefined) {
					frappe.show_alert({
						message: __("Parsed {0} rows.", [r.message.total_rows]),
						indicator: "green",
					});
				}
				frm.reload_doc();
			},
		});
	});
}
