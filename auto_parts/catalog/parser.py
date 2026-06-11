# Copyright (c) 2026, Masood Javid and contributors

"""ACES/PIES XML parsers.

PIES files describe product (Item) attributes, ACES files describe vehicle
fitment applications. Both formats are XML and may carry an XML namespace, so
tags are matched on their local name only.
"""

import xml.etree.ElementTree as ET


def _local(tag: str) -> str:
	"""Return an element tag without its namespace prefix."""
	return tag.split("}", 1)[-1] if "}" in tag else tag


def _find(element, name):
	for child in element:
		if _local(child.tag) == name:
			return child
	return None


def _find_all(element, name):
	return [child for child in element.iter() if _local(child.tag) == name]


def _text(element, name):
	child = _find(element, name)
	if child is not None and child.text:
		return child.text.strip()
	return ""


def _root_from_content(content):
	if isinstance(content, bytes):
		content = content.decode("utf-8", errors="replace")
	return ET.fromstring(content)


def parse_pies(content) -> list[dict]:
	"""Parse a PIES XML document into staging rows for Item creation.

	Each returned dict carries the part number, brand, PCdb part terminology
	and description used to create or update an Item.
	"""
	root = _root_from_content(content)
	rows = []

	for item in _find_all(root, "Item"):
		part_number = _text(item, "PartNumber") or _text(item, "PartNo")
		if not part_number:
			continue

		brand = (
			_text(item, "BrandAAIAID")
			or _text(item, "BrandLabel")
			or _element_attr(item, "Brand", "id")
			or _element_text(item, "Brand")
		)
		part_terminology = (
			_text(item, "PartTerminologyID")
			or _text(item, "PartTerminologyName")
			or _element_attr(item, "PartTerminology", "id")
			or _element_text(item, "PartTerminology")
		)

		description = ""
		descriptions = _find(item, "Descriptions")
		if descriptions is not None:
			preferred = None
			first = None
			for desc in _find_all(descriptions, "Description"):
				if first is None and desc.text:
					first = desc.text.strip()
				code = desc.get("DescriptionCode") or desc.get("MaintenanceType")
				if code in ("DES", "SHO", "MKT") and desc.text:
					preferred = desc.text.strip()
					break
			description = preferred or first or ""

		rows.append(
			{
				"raw_sku": part_number,
				"brand": brand,
				"part_terminology": part_terminology,
				"description": description,
			}
		)

	return rows


def parse_aces(content) -> list[dict]:
	"""Parse an ACES XML document into staging rows for Part Fitment creation.

	Each ``App`` element is one fitment application linking a part to a vehicle.
	Vehicle references (Make/Model/etc.) are read from a ``name`` attribute when
	present, otherwise the VCdb ``id`` attribute, otherwise the element text.
	"""
	root = _root_from_content(content)
	rows = []

	for app in _find_all(root, "App"):
		part_el = _find(app, "Part")
		part_number = (part_el.text or "").strip() if part_el is not None else ""
		if not part_number:
			continue

		base_vehicle = _find(app, "BaseVehicle")
		base_vehicle_id = base_vehicle.get("id") if base_vehicle is not None else ""

		year = ""
		years = _find(app, "Years")
		if years is not None:
			year = years.get("from") or years.get("to") or ""
		elif base_vehicle is not None:
			year = base_vehicle.get("year") or ""
		if not year:
			year = _vcdb_value(_find(app, "Year"))

		qualifier_ids, qualifiers = _parse_qualifiers(app)

		row = {
			"raw_sku": part_number,
			"aces_record_id": app.get("id") or "",
			"aces_action": (app.get("action") or "A").strip().upper(),
			"base_vehicle_id": base_vehicle_id or "",
			"year": _as_int(year),
			"make": _vcdb_value(_find(app, "Make")),
			"model": _vcdb_value(_find(app, "Model")),
			"submodel": _vcdb_value(_find(app, "SubModel")),
			"engine": _vcdb_value(_find(app, "EngineBase")) or _vcdb_value(_find(app, "Engine")),
			"position": _vcdb_value(_find(app, "Position")),
			"qty": _as_int(_text(app, "Qty")) or 1,
			"qualifier_ids": qualifier_ids,
			"qualifiers": qualifiers,
		}
		rows.append(row)

	return rows


def _parse_qualifiers(app):
	"""Read ACES ``Qual`` elements (Qdb) into id and human-readable strings."""
	ids = []
	texts = []
	for qual in _find_all(app, "Qual"):
		qid = (qual.get("id") or "").strip()
		text = _text(qual, "text")
		params = [p.get("value") for p in _find_all(qual, "param") if p.get("value")]
		if text and params:
			text = "{0} ({1})".format(text, ", ".join(params))
		elif params and not text:
			text = ", ".join(params)
		if qid:
			ids.append(qid)
		if text:
			texts.append(text)
	return ",".join(ids), "; ".join(texts)


def _element_text(element, name):
	child = _find(element, name)
	if child is not None and child.text:
		return child.text.strip()
	return ""


def _element_attr(element, name, attr):
	child = _find(element, name)
	if child is not None:
		return (child.get(attr) or "").strip()
	return ""


def _vcdb_value(element):
	if element is None:
		return ""
	return (element.get("name") or element.get("id") or (element.text or "")).strip()


def _as_int(value):
	try:
		return int(str(value).strip())
	except (TypeError, ValueError):
		return 0
