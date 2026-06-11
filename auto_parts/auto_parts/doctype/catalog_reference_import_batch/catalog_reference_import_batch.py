# Copyright (c) 2026, Masood Javid and contributors

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_files_path

from auto_parts.catalog.reference_import import import_reference_csv


class CatalogReferenceImportBatch(Document):
	def before_save(self):
		self.total_rows = len(self.import_lines or [])


@frappe.whitelist()
def enqueue_import(batch_name: str):
	frappe.db.set_value("Catalog Reference Import Batch", batch_name, "status", "Processing")
	frappe.enqueue(
		"auto_parts.auto_parts.doctype.catalog_reference_import_batch.catalog_reference_import_batch.run_import",
		queue="long",
		batch_name=batch_name,
		enqueue_after_commit=True,
	)
	return True


@frappe.whitelist()
def get_batch_status(batch_name: str):
	batch = frappe.db.get_value(
		"Catalog Reference Import Batch",
		batch_name,
		["status", "total_rows", "imported_rows", "failed_rows", "reference_type"],
		as_dict=True,
	)
	if not batch:
		frappe.throw(_("Import batch not found."))
	return batch


def run_import(batch_name: str):
	batch = frappe.get_doc("Catalog Reference Import Batch", batch_name)
	try:
		file_url = _resolve_import_file(batch)
		content = _read_attached_file(file_url)
		results = import_reference_csv(batch.reference_type, content)

		batch.set("import_lines", [])
		imported = failed = 0
		for result in results:
			if result["import_status"] == "Imported":
				imported += 1
			elif result["import_status"] == "Failed":
				failed += 1
			batch.append("import_lines", result)

		batch.total_rows = len(batch.import_lines)
		batch.imported_rows = imported
		batch.failed_rows = failed
		batch.status = "Failed" if failed and not imported else "Completed"
		batch.save(ignore_permissions=True)
	except Exception:
		frappe.db.rollback()
		frappe.db.set_value("Catalog Reference Import Batch", batch_name, "status", "Failed")
		frappe.log_error(title=f"Catalog reference import failed: {batch_name}")
		frappe.db.commit()
		raise


def _resolve_import_file(batch) -> str:
	if batch.import_file:
		return batch.import_file

	file_url = frappe.db.get_value(
		"File",
		{"attached_to_doctype": batch.doctype, "attached_to_name": batch.name},
		"file_url",
		order_by="creation desc",
	)
	if file_url:
		batch.db_set("import_file", file_url)
		return file_url

	frappe.throw(_("Please attach a CSV file first."))


def _read_attached_file(file_url: str):
	file_name = frappe.db.get_value("File", {"file_url": file_url}, "name")
	if file_name:
		return frappe.get_doc("File", file_name).get_content()

	path = get_files_path(file_url.split("/files/")[-1], is_private=file_url.startswith("/private"))
	with open(path, "rb") as f:
		return f.read()
