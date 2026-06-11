# Copyright (c) 2026, Masood Javid and contributors

"""Shopify marketplace connector.

LIVE API: replace stub methods with Shopify Admin REST/GraphQL calls once
client provides store URL and access token.
Docs: https://shopify.dev/docs/api/admin-rest
"""

from auto_parts.marketplace.base_connector import BaseMarketplaceConnector


class ShopifyConnector(BaseMarketplaceConnector):
	channel_name = "Shopify"

	def test_connection(self) -> dict:
		if not self.is_configured():
			return self.not_configured_result()
		# LIVE API: GET {store_url}/admin/api/2024-01/shop.json
		return self.dry_run_result("Connection test", store_url=self.channel.store_url)

	def push_inventory(self, listing, qty: float, price: float) -> dict:
		if not self.is_configured():
			return self.not_configured_result()
		# LIVE API: PUT /admin/api/.../inventory_levels/set.json
		# LIVE API: PUT /admin/api/.../variants/{id}.json for price
		return self.dry_run_result(
			"Inventory push",
			listing_id=listing.external_listing_id,
			qty=qty,
			price=price,
		)

	def pull_orders(self, since=None) -> list[dict]:
		if not self.is_configured():
			return []
		# LIVE API: GET /admin/api/.../orders.json?status=open&created_at_min=...
		return []
