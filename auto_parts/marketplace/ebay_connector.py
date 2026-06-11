# Copyright (c) 2026, Masood Javid and contributors

"""eBay marketplace connector.

LIVE API: replace push_inventory / pull_orders / test_connection bodies with
eBay Inventory API + Fulfillment API calls once client provides OAuth tokens.
Docs: https://developer.ebay.com/api-docs/sell/inventory/overview.html
"""

from auto_parts.marketplace.base_connector import BaseMarketplaceConnector


class EbayConnector(BaseMarketplaceConnector):
	channel_name = "eBay"

	def test_connection(self) -> dict:
		if not self.is_configured():
			return self.not_configured_result()
		# LIVE API: call eBay GET /sell/inventory/v1/inventory_item to verify token
		return self.dry_run_result("Connection test", seller_id=self.channel.seller_id)

	def push_inventory(self, listing, qty: float, price: float) -> dict:
		if not self.is_configured():
			return self.not_configured_result()
		# LIVE API: PUT /sell/inventory/v1/inventory_item/{sku}
		# LIVE API: POST /sell/inventory/v1/offer publish with quantity + price
		return self.dry_run_result(
			"Inventory push",
			listing_id=listing.external_listing_id,
			qty=qty,
			price=price,
		)

	def pull_orders(self, since=None) -> list[dict]:
		if not self.is_configured():
			return []
		# LIVE API: GET /sell/fulfillment/v1/order with filter creationdate
		return []
