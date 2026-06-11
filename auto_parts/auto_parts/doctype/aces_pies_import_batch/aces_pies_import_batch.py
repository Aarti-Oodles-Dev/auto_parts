# Copyright (c) 2026, Masood Javid and contributors

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_files_path

from auto_parts.catalog import parser
from auto_parts.catalog.resolver import enrich_aces_row, enrich_pies_row
from auto_parts.catalog.terminology import map_terminology_to_item_group

DEFAULT_STOCK_UOM = "Nos"
PROMOTABLE_STATUSES = ("Validated", "Pending")


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


@frappe.whitelist()
def get_batch_status(batch_name: str):
	"""Lightweight status poll used by the form while background jobs run."""
	batch = frappe.db.get_value(
		"ACES PIES Import Batch",
		batch_name,
		["status", "total_rows", "import_type"],
		as_dict=True,
	)
	if not batch:
		frappe.throw(_("Import batch not found."))
	return batch


def parse_import_file(batch_name: str):
	"""Read the attached XML file and load staging lines."""
	batch = frappe.get_doc("ACES PIES Import Batch", batch_name)
	try:
		file_url = _resolve_import_file(batch)
		content = _read_attached_file(file_url)

		if batch.import_type == "PIES":
			rows = [enrich_pies_row(row) for row in parser.parse_pies(content)]
		elif batch.import_type == "ACES":
			rows = [enrich_aces_row(row) for row in parser.parse_aces(content)]
		else:
			frappe.throw(_("Unknown import type: {0}").format(batch.import_type))

		batch.set("import_lines", [])
		seen_keys = set()
		for row in rows:
			status, message = _staging_status_for_row(row, seen_keys)
			row["import_status"] = status
			if message:
				row["error_message"] = message
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
		if line.import_status == "Promoted":
			_update_line(line, status="Skipped", error=_("Already promoted"))
			continue

		if line.import_status not in PROMOTABLE_STATUSES:
			continue

		savepoint = "ap_promote_line"
		frappe.db.savepoint(savepoint)
		try:
			if batch.import_type == "PIES":
				result = _promote_pies_line(line)
			else:
				result = _promote_aces_line(line)

			_update_line(
				line,
				status=result["status"],
				target_item=result.get("target_item"),
				target_fitment=result.get("target_fitment"),
				error=result.get("message", ""),
			)
		except Exception as exc:
			frappe.db.rollback(save_point=savepoint)
			_update_line(line, status="Failed", error=str(exc))

	frappe.db.set_value("ACES PIES Import Batch", batch_name, "status", "Completed")


def _staging_status_for_row(row: dict, seen_keys: set) -> tuple[str, str]:
	"""Assign Validated or Skipped while parsing staging lines."""
	if row.get("aces_action") == "D":
		return "Skipped", _("ACES delete action — row not promoted")

	dedupe_key = _staging_dedupe_key(row)
	if dedupe_key in seen_keys:
		return "Skipped", _("Duplicate row in import file")
	seen_keys.add(dedupe_key)
	return "Validated", ""


def _staging_dedupe_key(row: dict) -> tuple:
	return (
		row.get("raw_sku") or "",
		row.get("aces_record_id") or "",
		row.get("year") or 0,
		row.get("make") or "",
		row.get("model") or "",
		row.get("position") or "",
		row.get("qualifiers") or "",
	)


def _promote_result(status, target_item=None, target_fitment=None, message=""):
	return {
		"status": status,
		"target_item": target_item,
		"target_fitment": target_fitment,
		"message": message,
	}


def _update_line(line, status, target_item=None, target_fitment=None, error=None):
	values = {"import_status": status}
	if target_item is not None:
		values["target_item"] = target_item
	if target_fitment is not None:
		values["target_fitment"] = target_fitment
	if error is not None:
		values["error_message"] = error
	frappe.db.set_value("ACES PIES Import Line", line.name, values, update_modified=False)


def _promote_pies_line(line) -> dict:
	part_number = (line.raw_sku or "").strip()
	if not part_number:
		frappe.throw(_("Missing part number."))

	item_group = map_terminology_to_item_group(line.part_terminology)

	existing = frappe.db.get_value("Item", {"item_code": part_number}, "name")
	if not existing:
		existing = frappe.db.get_value("Item", {"manufacturer_part_number": part_number}, "name")

	if existing and not _pies_line_has_changes(line, existing):
		return _promote_result(
			"Skipped",
			target_item=existing,
			message=_("Item already up to date"),
		)

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
	term_id = getattr(line, "part_terminology_id", None) or line.part_terminology
	if term_id:
		item.part_terminology_id = term_id
	item.catalog_source = "ACES/PIES"
	item.save(ignore_permissions=True)
	return _promote_result("Promoted", target_item=item.name)


def _pies_line_has_changes(line, item_code: str) -> bool:
	item = frappe.db.get_value(
		"Item",
		item_code,
		["item_name", "item_group", "description", "aaia_brand_id", "part_terminology_id"],
		as_dict=True,
	)
	if not item:
		return True

	description = (line.description or "").strip()
	part_terminology = (line.part_terminology or "").strip()
	brand = (line.brand or "").strip()
	item_group = map_terminology_to_item_group(line.part_terminology)
	expected_name = (description or line.raw_sku)[:140]

	return any(
		[
			item.item_name != expected_name,
			item.item_group != item_group,
			(description and item.description != description),
			(brand and item.aaia_brand_id != brand),
			(part_terminology and item.part_terminology_id != part_terminology),
		]
	)


def _promote_aces_line(line) -> dict:
	part_number = (line.raw_sku or "").strip()
	if not part_number:
		frappe.throw(_("Missing part number."))

	if (line.aces_action or "").upper() == "D":
		return _promote_result("Skipped", message=_("ACES delete action — row not promoted"))

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
		return _promote_result(
			"Skipped",
			target_item=item_code,
			target_fitment=existing,
			message=_("Fitment already exists"),
		)

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
	return _promote_result("Promoted", target_item=item_code, target_fitment=fitment.name)


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
