# Copyright (c) 2026, Masood Javid and contributors

"""Resolve VCdb/PCdb/Qdb IDs to human-readable values during catalog import."""

import frappe
from frappe.utils import cint


def _is_numeric_id(value: str | None) -> bool:
	value = (value or "").strip()
	return bool(value) and value.isdigit()


def lookup_part_terminology(value: str | None) -> tuple[str, str]:
	"""Return (terminology_id, terminology_name) for a PCdb id or name."""
	raw = (value or "").strip()
	if not raw:
		return "", ""

	if frappe.db.exists("PCdb Part Terminology", raw):
		name = frappe.db.get_value("PCdb Part Terminology", raw, "part_terminology_name") or raw
		return raw, name

	by_id = frappe.db.get_value(
		"PCdb Part Terminology",
		{"part_terminology_id": raw},
		["part_terminology_id", "part_terminology_name"],
		as_dict=True,
	)
	if by_id:
		return by_id.part_terminology_id, by_id.part_terminology_name or raw

	by_name = frappe.db.get_value(
		"PCdb Part Terminology",
		{"part_terminology_name": raw},
		["part_terminology_id", "part_terminology_name"],
		as_dict=True,
	)
	if by_name:
		return by_name.part_terminology_id, by_name.part_terminology_name or raw

	if _is_numeric_id(raw):
		return raw, raw
	return raw, raw


def lookup_make(value: str | None) -> str:
	raw = (value or "").strip()
	if not raw:
		return ""

	if not _is_numeric_id(raw):
		return raw

	if frappe.db.exists("VCdb Make", raw):
		return frappe.db.get_value("VCdb Make", raw, "make_name") or raw

	return (
		frappe.db.get_value("VCdb Make", {"make_id": raw}, "make_name")
		or raw
	)


def lookup_model(value: str | None) -> str:
	raw = (value or "").strip()
	if not raw:
		return ""

	if not _is_numeric_id(raw):
		return raw

	if frappe.db.exists("VCdb Model", raw):
		return frappe.db.get_value("VCdb Model", raw, "model_name") or raw

	return (
		frappe.db.get_value("VCdb Model", {"model_id": raw}, "model_name")
		or raw
	)


def lookup_base_vehicle(vcdb_id: str | None) -> dict | None:
	raw = (vcdb_id or "").strip()
	if not raw:
		return None

	name = raw if frappe.db.exists("VCdb Base Vehicle", raw) else None
	if not name:
		name = frappe.db.get_value("VCdb Base Vehicle", {"vcdb_id": raw}, "name")
	if not name:
		return None

	return frappe.db.get_value(
		"VCdb Base Vehicle",
		name,
		["vcdb_id", "year", "make_id", "make", "model_id", "model", "submodel", "engine"],
		as_dict=True,
	)


def lookup_qualifier(qualifier_id: str | None) -> str:
	raw = (qualifier_id or "").strip()
	if not raw:
		return ""

	if frappe.db.exists("Qdb Qualifier", raw):
		return frappe.db.get_value("Qdb Qualifier", raw, "qualifier_description") or raw

	return (
		frappe.db.get_value("Qdb Qualifier", {"qualifier_id": raw}, "qualifier_description")
		or raw
	)


def resolve_qualifiers(qualifier_ids: str | None, qualifiers: str | None = None) -> str:
	if qualifiers and not _is_numeric_id(qualifiers.split(";")[0].strip()):
		return qualifiers

	ids = [part.strip() for part in (qualifier_ids or "").split(",") if part.strip()]
	if not ids:
		return qualifiers or ""

	texts = []
	for qid in ids:
		text = lookup_qualifier(qid)
		if text and text != qid:
			texts.append(text)
		elif qualifiers:
			continue
		else:
			texts.append(qid)
	return "; ".join(texts)


def enrich_pies_row(row: dict) -> dict:
	term_id, term_name = lookup_part_terminology(row.get("part_terminology"))
	if term_id:
		row["part_terminology_id"] = term_id
	if term_name:
		row["part_terminology"] = term_name
	return row


def enrich_aces_row(row: dict) -> dict:
	base_vehicle = lookup_base_vehicle(row.get("base_vehicle_id"))
	if base_vehicle:
		if not row.get("year"):
			row["year"] = cint(base_vehicle.year)
		if not row.get("make") or _is_numeric_id(row.get("make")):
			row["make"] = base_vehicle.make or lookup_make(base_vehicle.make_id or row.get("make"))
		if not row.get("model") or _is_numeric_id(row.get("model")):
			row["model"] = base_vehicle.model or lookup_model(base_vehicle.model_id or row.get("model"))
		if not row.get("submodel") and base_vehicle.submodel:
			row["submodel"] = base_vehicle.submodel
		if not row.get("engine") and base_vehicle.engine:
			row["engine"] = base_vehicle.engine

	if _is_numeric_id(row.get("make")):
		row["make"] = lookup_make(row.get("make"))
	if _is_numeric_id(row.get("model")):
		row["model"] = lookup_model(row.get("model"))
	if _is_numeric_id(row.get("submodel")):
		row["submodel"] = lookup_model(row.get("submodel")) or row.get("submodel")
	if _is_numeric_id(row.get("engine")):
		row["engine"] = row.get("engine")
	if _is_numeric_id(row.get("position")):
		row["position"] = row.get("position")

	row["qualifiers"] = resolve_qualifiers(row.get("qualifier_ids"), row.get("qualifiers"))
	return row
