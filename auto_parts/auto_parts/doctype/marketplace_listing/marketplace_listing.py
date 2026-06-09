from frappe.model.document import Document
import frappe
from frappe.utils import flt
# auto_parts/doctype/marketplace_listing/marketplace_listing.py
class MarketplaceListing(Document):
    def before_save(self):
        if self.pricing_method == 'Cost Plus':
            self.calculate_channel_price()

    def calculate_channel_price(self):
        # Item ka average cost lo
        avg_cost = frappe.db.get_value(
            'Item',
            self.item_code,
            'valuation_rate'
        ) or 0

        if not avg_cost:
            frappe.throw(f'No valuation rate found for {self.item_code}')

        markup = flt(self.channel_markup_percent) / 100
        self.listing_price = flt(avg_cost) * (1 + markup)
        self.listing_price = round(self.listing_price, 2)