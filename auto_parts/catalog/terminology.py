# Copyright (c) 2026, Masood Javid and contributors

"""Map PCdb part terminology to an ERPNext Item Group.

A PIES part terminology (PCdb) value is turned into an Item Group so that
imported parts are categorised consistently. Groups are created on demand
under the root "All Item Groups" node.
"""

import frappe
from frappe import _

from auto_parts.catalog.resolver import lookup_part_terminology

DEFAULT_ITEM_GROUP = "Products"


def _root_item_group() -> str:
	root = frappe.db.get_value("Item Group", {"is_group": 1, "parent_item_group": ""}, "name")
	return root or "All Item Groups"


def _fallback_item_group() -> str:
	if frappe.db.exists("Item Group", DEFAULT_ITEM_GROUP):
		return DEFAULT_ITEM_GROUP
	leaf = frappe.db.get_value("Item Group", {"is_group": 0}, "name")
	return leaf or _root_item_group()


def _lookup_pcdb_mapping(part_terminology: str) -> str | None:
	"""Resolve a PCdb id or name via the admin mapping table."""
	mapping = frappe.db.get_value(
		"PCdb Terminology Mapping",
		{"part_terminology_id": part_terminology},
		"item_group",
	)
	if mapping:
		return mapping

	return frappe.db.get_value(
		"PCdb Terminology Mapping",
		{"part_terminology_name": part_terminology},
		"item_group",
	)


def map_terminology_to_item_group(part_terminology: str | None) -> str:
	"""Return the Item Group for a PCdb terminology, creating it if needed."""
	terminology = (part_terminology or "").strip()
	if not terminology:
		return _fallback_item_group()

	term_id, term_name = lookup_part_terminology(terminology)
	for candidate in (term_id, term_name, terminology):
		if not candidate:
			continue
		mapped = _lookup_pcdb_mapping(candidate)
		if mapped:
			return mapped

	group_name = term_name or term_id or terminology
	group_name = group_name if len(group_name) <= 140 else group_name[:140]

	if frappe.db.exists("Item Group", group_name):
		return group_name

	doc = frappe.get_doc(
		{
			"doctype": "Item Group",
			"item_group_name": group_name,
			"parent_item_group": _root_item_group(),
			"is_group": 0,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name
