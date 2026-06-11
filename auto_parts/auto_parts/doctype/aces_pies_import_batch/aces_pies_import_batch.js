// Copyright (c) 2026, Masood Javid and contributors

let parse_poll_timer = null;

frappe.ui.form.on("ACES PIES Import Batch", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}

		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Parse File"), () => enqueue_parse_import_file(frm)).addClass(
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
				__("Processing in background... this page will refresh automatically.")
			);
			start_parse_poll(frm);
		} else {
			stop_parse_poll();
		}
	},

	onload(frm) {
		if (frm.doc.status === "Processing") {
			start_parse_poll(frm);
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

function enqueue_parse_import_file(frm) {
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
				"auto_parts.auto_parts.doctype.aces_pies_import_batch.aces_pies_import_batch.enqueue_parse",
			args: { batch_name: frm.doc.name },
			freeze: true,
			freeze_message: __("Queuing XML parse job..."),
			callback() {
				frm.reload_doc().then(() => start_parse_poll(frm));
			},
		});
	});
}

function start_parse_poll(frm) {
	stop_parse_poll();
	parse_poll_timer = setInterval(() => poll_batch_status(frm), 3000);
}

function stop_parse_poll() {
	if (parse_poll_timer) {
		clearInterval(parse_poll_timer);
		parse_poll_timer = null;
	}
}

function poll_batch_status(frm) {
	frappe.call({
		method:
			"auto_parts.auto_parts.doctype.aces_pies_import_batch.aces_pies_import_batch.get_batch_status",
		args: { batch_name: frm.doc.name },
		callback(r) {
			const status = r.message?.status;
			if (!status || status === "Processing") {
				return;
			}

			stop_parse_poll();
			frm.reload_doc().then(() => {
				if (status === "Draft" && r.message?.total_rows) {
					frappe.show_alert({
						message: __("Parsed {0} rows.", [r.message.total_rows]),
						indicator: "green",
					});
				} else if (status === "Failed") {
					frappe.msgprint({
						title: __("Parse Failed"),
						message: __("Check the Error Log for details."),
						indicator: "red",
					});
				}
			});
		},
	});
}
