# Copyright (c) 2026, Masood Javid and contributors

"""Base connector for marketplace channels.

Each platform connector inherits from BaseMarketplaceConnector.
When the client provides API credentials, replace the stub methods
marked LIVE API in ebay_connector.py / amazon_connector.py / shopify_connector.py.
"""

from abc import ABC, abstractmethod

import frappe
from frappe import _


class ConnectorNotConfiguredError(Exception):
	pass


class BaseMarketplaceConnector(ABC):
	channel_name: str = ""

	def __init__(self, channel_doc):
		self.channel = channel_doc

	def get_api_key(self) -> str | None:
		if not self.channel.api_key:
			return None
		return self.channel.get_password("api_key")

	def get_api_secret(self) -> str | None:
		if not self.channel.api_secret:
			return None
		return self.channel.get_password("api_secret")

	def is_configured(self) -> bool:
		"""Credentials present enough to attempt a live API call."""
		if self.channel_name == "Shopify":
			return bool(self.get_api_key() and self.channel.store_url)
		return bool(self.get_api_key() and self.channel.seller_id)

	def not_configured_result(self) -> dict:
		return {
			"success": False,
			"message": _("API credentials not configured for {0}. Add them in Marketplace Channel.").format(
				self.channel_name
			),
		}

	def dry_run_result(self, action: str, **extra) -> dict:
		"""Return success for internal pipeline testing before live API is wired."""
		return {
			"success": True,
			"simulated": True,
			"message": _("{0} dry-run OK for {1}. Implement LIVE API in the connector file.").format(
				action,
				self.channel_name,
			),
			**extra,
		}

	@abstractmethod
	def test_connection(self) -> dict:
		pass

	@abstractmethod
	def push_inventory(self, listing, qty: float, price: float) -> dict:
		pass

	@abstractmethod
	def pull_orders(self, since=None) -> list[dict]:
		pass
