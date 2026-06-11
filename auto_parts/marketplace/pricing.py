# Copyright (c) 2026, Masood Javid and contributors

"""Dynamic marketplace pricing (PDF: Cost-plus and dynamic marketplace pricing)."""

import frappe
from frappe import _
from frappe.utils import flt


def calculate_listing_price(listing) -> float:
	"""Return the price to push for a marketplace listing."""
	method = listing.pricing_method or "Cost Plus"

	if method == "Fixed":
		return flt(listing.listing_price)

	if method == "Price List":
		price_list = listing.price_list
		if not price_list:
			frappe.throw(_("Price List is required when pricing method is Price List."))
		rate = frappe.db.get_value(
			"Item Price",
			{"item_code": listing.item, "price_list": price_list, "selling": 1},
			"price_list_rate",
		)
		if rate is None:
			frappe.throw(_("No Item Price found for {0} in {1}.").format(listing.item, price_list))
		return flt(rate)

	# Cost Plus (default)
	avg_cost = frappe.db.get_value("Item", listing.item, "valuation_rate") or 0
	if not avg_cost:
		avg_cost = frappe.db.get_value("Item", listing.item, "standard_rate") or 0
	if not avg_cost:
		frappe.throw(_("No valuation rate found for {0}.").format(listing.item))

	markup = flt(listing.channel_markup_percent) / 100
	return round(flt(avg_cost) * (1 + markup), 2)
