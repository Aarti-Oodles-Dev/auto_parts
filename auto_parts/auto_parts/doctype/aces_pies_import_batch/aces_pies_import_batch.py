# Copyright (c) 2026, Masood Javid and contributors

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_files_path

from auto_parts.catalog import parser
from auto_parts.catalog.terminology import map_terminology_to_item_group

DEFAULT_STOCK_UOM = "Nos"


class ACESPIESImportBatch(Document):
	def before_save(self):
		self.total_rows = len(self.import_lines or [])

	def on_submit(self):
		"""Submitting the batch promotes staged rows to Items / Fitment."""
		self.db_set("status", "Processing")
		frappe.enqueue(
			"auto_parts.auto_parts.doctype.aces_pies_import_batch.aces_pies_import_batch.promote_batch",
			queue="long",
			batch_name=self.name,
			enqueue_after_commit=True,
		)


# ---------------------------------------------------------------------------
# Parsing (staging) -- task: background job parse XML to import lines
# ---------------------------------------------------------------------------


@frappe.whitelist()
def enqueue_parse(batch_name: str):
	"""Queue the parse job for a batch and mark it as processing."""
	frappe.db.set_value("ACES PIES Import Batch", batch_name, "status", "Processing")
	frappe.enqueue(
		"auto_parts.auto_parts.doctype.aces_pies_import_batch.aces_pies_import_batch.parse_import_file",
		queue="long",
		batch_name=batch_name,
		enqueue_after_commit=True,
	)
	return True


@frappe.whitelist()
def parse_import_file_now(batch_name: str):
	"""Parse the attached XML immediately (works for both ACES and PIES)."""
	parse_import_file(batch_name)
	batch = frappe.get_doc("ACES PIES Import Batch", batch_name)
	return {"total_rows": batch.total_rows, "import_type": batch.import_type}


def parse_import_file(batch_name: str):
	"""Read the attached XML file and load staging lines."""
	batch = frappe.get_doc("ACES PIES Import Batch", batch_name)
	try:
		file_url = _resolve_import_file(batch)
		content = _read_attached_file(file_url)

		if batch.import_type == "PIES":
			rows = parser.parse_pies(content)
		elif batch.import_type == "ACES":
			rows = parser.parse_aces(content)
		else:
			frappe.throw(_("Unknown import type: {0}").format(batch.import_type))

		batch.set("import_lines", [])
		for row in rows:
			row["import_status"] = "Pending"
			batch.append("import_lines", row)

		batch.total_rows = len(batch.import_lines)
		batch.status = "Draft"
		batch.save(ignore_permissions=True)
	except Exception:
		frappe.db.rollback()
		frappe.db.set_value("ACES PIES Import Batch", batch_name, "status", "Failed")
		frappe.log_error(title=f"ACES/PIES parse failed: {batch_name}")
		frappe.db.commit()
		raise


def _resolve_import_file(batch) -> str:
	"""Return import_file URL, falling back to the latest attachment on the batch."""
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

	frappe.throw(_("Please attach an import file first."))


def _read_attached_file(file_url: str):
	file_name = frappe.db.get_value("File", {"file_url": file_url}, "name")
	if file_name:
		return frappe.get_doc("File", file_name).get_content()

	path = get_files_path(file_url.split("/files/")[-1], is_private=file_url.startswith("/private"))
	with open(path, "rb") as f:
		return f.read()


# ---------------------------------------------------------------------------
# Promotion -- task: create/update Item and Part Fitment from staging
# ---------------------------------------------------------------------------


def promote_batch(batch_name: str):
	"""Promote staged rows to Items (PIES) or Part Fitment (ACES).

	Each line is wrapped in a savepoint so a single bad row is marked Failed
	without rolling back rows that were promoted successfully.
	"""
	batch = frappe.get_doc("ACES PIES Import Batch", batch_name)

	for line in batch.import_lines:
		savepoint = "ap_promote_line"
		frappe.db.savepoint(savepoint)
		try:
			if batch.import_type == "PIES":
				item_code = _promote_pies_line(line)
				_update_line(line, status="Promoted", target_item=item_code, error="")
			else:
				item_code, fitment = _promote_aces_line(line)
				_update_line(
					line,
					status="Promoted",
					target_item=item_code,
					target_fitment=fitment,
					error="",
				)
		except Exception as exc:
			frappe.db.rollback(save_point=savepoint)
			_update_line(line, status="Failed", error=str(exc))

	frappe.db.set_value("ACES PIES Import Batch", batch_name, "status", "Completed")


def _update_line(line, status, target_item=None, target_fitment=None, error=None):
	values = {"import_status": status}
	if target_item is not None:
		values["target_item"] = target_item
	if target_fitment is not None:
		values["target_fitment"] = target_fitment
	if error is not None:
		values["error_message"] = error
	frappe.db.set_value("ACES PIES Import Line", line.name, values, update_modified=False)


def _promote_pies_line(line) -> str:
	part_number = (line.raw_sku or "").strip()
	if not part_number:
		frappe.throw(_("Missing part number."))

	item_group = map_terminology_to_item_group(line.part_terminology)

	existing = frappe.db.get_value("Item", {"item_code": part_number}, "name")
	if not existing:
		existing = frappe.db.get_value("Item", {"manufacturer_part_number": part_number}, "name")

	if existing:
		item = frappe.get_doc("Item", existing)
	else:
		item = frappe.new_doc("Item")
		item.item_code = part_number
		item.stock_uom = DEFAULT_STOCK_UOM

	item.item_name = (line.description or part_number)[:140]
	item.item_group = item_group
	if line.description:
		item.description = line.description
	item.manufacturer_part_number = part_number
	if line.brand:
		item.aaia_brand_id = line.brand
	if line.part_terminology:
		item.part_terminology_id = line.part_terminology
	item.catalog_source = "ACES/PIES"
	item.save(ignore_permissions=True)
	return item.name


def _promote_aces_line(line):
	part_number = (line.raw_sku or "").strip()
	if not part_number:
		frappe.throw(_("Missing part number."))

	item_code = frappe.db.get_value("Item", {"item_code": part_number}, "name")
	if not item_code:
		item_code = frappe.db.get_value("Item", {"manufacturer_part_number": part_number}, "name")
	if not item_code:
		frappe.throw(
			_("Item {0} not found. Import the PIES catalog before ACES fitment.").format(part_number)
		)

	vehicle_config = _resolve_vehicle_configuration(line)
	position = (line.position or "").strip()
	qualifiers = (line.qualifiers or "").strip()

	existing = frappe.db.get_value(
		"Part Fitment",
		{
			"item": item_code,
			"vehicle_configuration": vehicle_config,
			"position": position,
			"qualifiers": qualifiers,
		},
		"name",
	)
	if existing:
		return item_code, existing

	fitment = frappe.get_doc(
		{
			"doctype": "Part Fitment",
			"item": item_code,
			"vehicle_configuration": vehicle_config,
			"position": position,
			"qty": line.qty or 1,
			"source": "ACES/PIES",
			"aces_record_id": line.aces_record_id or "",
			"qualifier_ids": line.qualifier_ids or "",
			"qualifiers": qualifiers,
		}
	)
	fitment.insert(ignore_permissions=True)
	return item_code, fitment.name


def _resolve_vehicle_configuration(line) -> str:
	if line.base_vehicle_id:
		existing = frappe.db.get_value(
			"Vehicle Configuration", {"vcdb_id": line.base_vehicle_id}, "name"
		)
		if existing:
			return existing

	filters = {
		"year": line.year or 0,
		"make": line.make or "",
		"model": line.model or "",
		"submodel": line.submodel or "",
		"engine": line.engine or "",
	}
	existing = frappe.db.get_value("Vehicle Configuration", filters, "name")
	if existing:
		return existing

	if not (line.year and line.make and line.model):
		frappe.throw(_("Insufficient vehicle data to build a Vehicle Configuration."))

	config = frappe.get_doc(
		{
			"doctype": "Vehicle Configuration",
			"year": line.year,
			"make": line.make,
			"model": line.model,
			"submodel": line.submodel or "",
			"engine": line.engine or "",
			"vcdb_id": line.base_vehicle_id or "",
		}
	)
	config.insert(ignore_permissions=True)
	return config.name
