# Copyright (c) 2026, Masood Javid and contributors

import frappe
from frappe.model.document import Document
from frappe.utils import flt

from auto_parts.marketplace.pricing import calculate_listing_price


class MarketplaceListing(Document):
	def before_save(self):
		if self.pricing_method in ("Cost Plus", "Price List"):
			self.listing_price = calculate_listing_price(self)

	@frappe.whitelist()
	def calculate_channel_price(self):
		self.listing_price = calculate_listing_price(self)
		return flt(self.listing_price)
