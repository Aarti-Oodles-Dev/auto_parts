# Copyright (c) 2026, Masood Javid and contributors

"""Import VCdb/PCdb/Qdb reference rows from CSV into master DocTypes."""

import csv
import io

import frappe
from frappe import _
from frappe.utils import cint


REFERENCE_CONFIG = {
	"PCdb Part Terminology": {
		"doctype": "PCdb Part Terminology",
		"key_field": "part_terminology_id",
		"required": ("part_terminology_id", "part_terminology_name"),
		"aliases": {
			"part_terminology_id": ("part_terminology_id", "partterminologyid", "id"),
			"part_terminology_name": (
				"part_terminology_name",
				"partterminologyname",
				"name",
				"description",
			),
		},
	},
	"Qdb Qualifier": {
		"doctype": "Qdb Qualifier",
		"key_field": "qualifier_id",
		"required": ("qualifier_id", "qualifier_description"),
		"aliases": {
			"qualifier_id": ("qualifier_id", "qualifierid", "id"),
			"qualifier_description": (
				"qualifier_description",
				"qualifierdescription",
				"description",
				"text",
			),
		},
	},
	"VCdb Make": {
		"doctype": "VCdb Make",
		"key_field": "make_id",
		"required": ("make_id", "make_name"),
		"aliases": {
			"make_id": ("make_id", "makeid", "id"),
			"make_name": ("make_name", "makename", "name"),
		},
	},
	"VCdb Model": {
		"doctype": "VCdb Model",
		"key_field": "model_id",
		"required": ("model_id", "model_name"),
		"aliases": {
			"model_id": ("model_id", "modelid", "id"),
			"model_name": ("model_name", "modelname", "name"),
			"make_id": ("make_id", "makeid"),
		},
	},
	"VCdb Base Vehicle": {
		"doctype": "VCdb Base Vehicle",
		"key_field": "vcdb_id",
		"required": ("vcdb_id",),
		"aliases": {
			"vcdb_id": ("vcdb_id", "basevehicleid", "base_vehicle_id", "id"),
			"year": ("year", "yearid"),
			"make_id": ("make_id", "makeid"),
			"make": ("make", "make_name", "makename"),
			"model_id": ("model_id", "modelid"),
			"model": ("model", "model_name", "modelname"),
			"submodel": ("submodel", "submodel_name"),
			"engine": ("engine", "enginebase", "engine_base"),
		},
	},
}


def import_reference_csv(reference_type: str, content) -> list[dict]:
	config = REFERENCE_CONFIG.get(reference_type)
	if not config:
		frappe.throw(_("Unsupported reference type: {0}").format(reference_type))

	rows = _read_csv_rows(content)
	if not rows:
		frappe.throw(_("CSV file is empty."))

	results = []
	for row in rows:
		results.append(_import_row(config, row))
	return results


def _read_csv_rows(content) -> list[dict]:
	if isinstance(content, bytes):
		content = content.decode("utf-8-sig", errors="replace")

	reader = csv.DictReader(io.StringIO(content))
	if not reader.fieldnames:
		return []

	normalized_fieldnames = [_normalize_header(name) for name in reader.fieldnames]
	rows = []
	for raw in reader:
		row = {}
		for original, normalized in zip(reader.fieldnames, normalized_fieldnames):
			value = (raw.get(original) or "").strip()
			if value:
				row[normalized] = value
		if row:
			rows.append(row)
	return rows


def _normalize_header(header: str) -> str:
	return (header or "").strip().lower().replace(" ", "_").replace("-", "_")


def _map_row(config: dict, row: dict) -> dict:
	mapped = {}
	for field, aliases in config["aliases"].items():
		for alias in aliases:
			if alias in row:
				mapped[field] = row[alias]
				break
	return mapped


def _import_row(config: dict, row: dict) -> dict:
	mapped = _map_row(config, row)
	key_value = (mapped.get(config["key_field"]) or "").strip()

	if not key_value:
		return {
			"reference_key": "",
			"import_status": "Failed",
			"error_message": _("Missing key column: {0}").format(config["key_field"]),
		}

	for field in config["required"]:
		if not (mapped.get(field) or "").strip():
			return {
				"reference_key": key_value,
				"import_status": "Failed",
				"error_message": _("Missing required column: {0}").format(field),
			}

	if config["doctype"] == "VCdb Base Vehicle" and mapped.get("year"):
		mapped["year"] = cint(mapped["year"])

	try:
		status = _upsert_reference(config["doctype"], config["key_field"], mapped)
		return {
			"reference_key": key_value,
			"import_status": status,
			"error_message": "",
		}
	except Exception as exc:
		return {
			"reference_key": key_value,
			"import_status": "Failed",
			"error_message": str(exc),
		}


def _upsert_reference(doctype: str, key_field: str, values: dict) -> str:
	key_value = values[key_field]
	existing = frappe.db.get_value(doctype, {key_field: key_value}, "name")

	if existing:
		doc = frappe.get_doc(doctype, existing)
		changed = False
		for field, value in values.items():
			if field == key_field:
				continue
			if doc.get(field) != value:
				doc.set(field, value)
				changed = True
		if changed:
			doc.save(ignore_permissions=True)
			return "Imported"
		return "Skipped"

	doc = frappe.get_doc({"doctype": doctype, **values})
	doc.insert(ignore_permissions=True)
	return "Imported"
