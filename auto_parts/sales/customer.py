# Copyright (c) 2026, Masood Javid and contributors

import frappe
from frappe import _

TIER_PRICE_LIST_MAP = {
	"Retail": "Retail",
	"Commercial": "Commercial",
	"Fleet": "Commercial",
}


def get_price_list_for_tier(pricing_tier: str | None) -> str | None:
	if not pricing_tier:
		return None

	price_list = TIER_PRICE_LIST_MAP.get(pricing_tier)
	if price_list and frappe.db.exists("Price List", price_list):
		return price_list

	return None


def validate_customer(doc, method=None):
	if not doc.pricing_tier:
		return

	price_list = get_price_list_for_tier(doc.pricing_tier)
	if not price_list:
		return

	before = doc.get_doc_before_save()
	tier_changed = not before or before.get("pricing_tier") != doc.pricing_tier

	# Sync when tier changes or default price list is empty (fixes Retail → Commercial)
	if tier_changed or not doc.default_price_list:
		doc.default_price_list = price_list


@frappe.whitelist()
def get_customer_commercial_details(customer: str) -> dict:
	if not customer:
		return {}

	details = frappe.db.get_value(
		"Customer",
		customer,
		["pricing_tier", "allow_buyout", "default_price_list"],
		as_dict=True,
	)

	price_list = get_price_list_for_tier(details.pricing_tier) or details.default_price_list
	return {
		"pricing_tier": details.pricing_tier,
		"allow_buyout": details.allow_buyout,
		"selling_price_list": price_list,
	}
