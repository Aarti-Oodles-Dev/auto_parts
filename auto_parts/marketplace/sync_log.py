# Copyright (c) 2026, Masood Javid and contributors

import frappe
from frappe.utils import now_datetime


def write_sync_log(
	listing_name: str | None,
	channel_name: str,
	direction: str,
	status: str,
	message: str,
) -> str:
	doc = frappe.get_doc(
		{
			"doctype": "Marketplace Sync Log",
			"marketplace_listing": listing_name,
			"marketplace_channel": channel_name,
			"sync_direction": direction,
			"status": status,
			"synced_on": now_datetime(),
			"message": message,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name
