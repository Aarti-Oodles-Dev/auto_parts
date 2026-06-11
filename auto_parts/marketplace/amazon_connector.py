# Copyright (c) 2026, Masood Javid and contributors

"""Amazon marketplace connector.

LIVE API: replace stub methods with Amazon SP-API calls once client provides
LWA refresh token, client id/secret, and marketplace id.
Docs: https://developer-docs.amazon.com/sp-api/
"""

from auto_parts.marketplace.base_connector import BaseMarketplaceConnector


class AmazonConnector(BaseMarketplaceConnector):
	channel_name = "Amazon"

	def test_connection(self) -> dict:
		if not self.is_configured():
			return self.not_configured_result()
		# LIVE API: call SP-API Sellers.getMarketplaceParticipations
		return self.dry_run_result("Connection test", seller_id=self.channel.seller_id)

	def push_inventory(self, listing, qty: float, price: float) -> dict:
		if not self.is_configured():
			return self.not_configured_result()
		# LIVE API: PATCH /listings/2021-08-01/items/{sellerId}/{sku}
		# LIVE API: POST /products/prices/v0/listings/{SellerSKU}/price
		return self.dry_run_result(
			"Inventory push",
			listing_id=listing.external_listing_id,
			qty=qty,
			price=price,
		)

	def pull_orders(self, since=None) -> list[dict]:
		if not self.is_configured():
			return []
		# LIVE API: GET /orders/v0/orders with CreatedAfter filter
		return []
