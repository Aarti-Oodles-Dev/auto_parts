# Copyright (c) 2026, Masood Javid and contributors

import frappe
from frappe.model.document import Document

from auto_parts.marketplace.factory import get_connector


class MarketplaceChannel(Document):
	pass


@frappe.whitelist()
def test_connection(channel_name: str):
	connector = get_connector(channel_name)
	return connector.test_connection()
