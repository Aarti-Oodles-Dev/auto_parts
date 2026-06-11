# Copyright (c) 2026, Masood Javid and contributors

import frappe
from frappe import _

from auto_parts.marketplace.amazon_connector import AmazonConnector
from auto_parts.marketplace.ebay_connector import EbayConnector
from auto_parts.marketplace.shopify_connector import ShopifyConnector

CONNECTOR_MAP = {
	"eBay": EbayConnector,
	"Amazon": AmazonConnector,
	"Shopify": ShopifyConnector,
}


def get_connector(channel_name: str):
	if not frappe.db.exists("Marketplace Channel", channel_name):
		frappe.throw(_("Marketplace Channel {0} not found.").format(channel_name))

	channel_doc = frappe.get_doc("Marketplace Channel", channel_name)
	connector_cls = CONNECTOR_MAP.get(channel_name)
	if not connector_cls:
		frappe.throw(_("No connector implemented for channel {0}.").format(channel_name))
	return connector_cls(channel_doc)
