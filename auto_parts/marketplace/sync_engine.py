# Copyright (c) 2026, Masood Javid and contributors

"""Marketplace stock sync scheduler and orchestration."""

import frappe
from frappe import _
from frappe.utils import now_datetime

from auto_parts.marketplace.factory import get_connector
from auto_parts.marketplace.order_import import import_marketplace_order
from auto_parts.marketplace.oversell import get_available_qty
from auto_parts.marketplace.pricing import calculate_listing_price
from auto_parts.marketplace.sync_log import write_sync_log


def is_sync_enabled() -> bool:
	return bool(frappe.db.get_single_value("Auto Parts Settings", "enable_marketplace_sync"))


def _get_channel_warehouse(channel_name: str) -> str | None:
	return frappe.db.get_value("Marketplace Channel", channel_name, "default_warehouse")


def sync_listing(listing_name: str) -> dict:
	"""Push stock and price for one marketplace listing."""
	listing = frappe.get_doc("Marketplace Listing", listing_name)
	channel_name = listing.marketplace_channel

	if listing.listing_status != "Active":
		write_sync_log(
			listing_name,
			channel_name,
			"Outbound",
			"Failed",
			_("Listing status is {0}; only Active listings are synced.").format(listing.listing_status),
		)
		return {"success": False, "message": _("Listing is not active.")}

	channel = frappe.db.get_value(
		"Marketplace Channel",
		channel_name,
		["enabled", "default_warehouse"],
		as_dict=True,
	)
	if not channel or not channel.enabled:
		write_sync_log(listing_name, channel_name, "Outbound", "Failed", _("Channel is disabled."))
		return {"success": False, "message": _("Channel is disabled.")}

	warehouse = channel.default_warehouse
	if not warehouse:
		write_sync_log(
			listing_name,
			channel_name,
			"Outbound",
			"Failed",
			_("Default warehouse not set on Marketplace Channel."),
		)
		return {"success": False, "message": _("Warehouse not configured.")}

	try:
		price = calculate_listing_price(listing)
		qty = get_available_qty(listing.item, warehouse, listing.qty_buffer)
	except Exception as exc:
		write_sync_log(listing_name, channel_name, "Outbound", "Failed", str(exc))
		listing.db_set("listing_status", "Error")
		return {"success": False, "message": str(exc)}

	connector = get_connector(channel_name)
	result = connector.push_inventory(listing, qty, price)

	status = "Success" if result.get("success") else "Failed"
	if result.get("simulated"):
		status = "Pending"

	message = result.get("message") or _("Sync completed.")
	write_sync_log(listing_name, channel_name, "Outbound", status, message)

	listing.db_set(
		{
			"last_synced_on": now_datetime(),
			"last_synced_qty": qty,
			"last_synced_price": price,
			"listing_price": price,
			"listing_status": "Active" if result.get("success") else "Error",
		}
	)

	return {"success": result.get("success"), "qty": qty, "price": price, "message": message}


def sync_all_listings():
	"""Sync every active listing on enabled channels."""
	if not is_sync_enabled():
		return

	listings = frappe.get_all(
		"Marketplace Listing",
		filters={"listing_status": "Active"},
		pluck="name",
	)
	for listing_name in listings:
		try:
			sync_listing(listing_name)
		except Exception:
			frappe.log_error(title=f"Marketplace sync failed for {listing_name}")


def sync_listings_for_item(item_code: str):
	"""Re-sync active listings when warehouse stock changes."""
	if not is_sync_enabled():
		return

	listings = frappe.get_all(
		"Marketplace Listing",
		filters={"item": item_code, "listing_status": "Active"},
		pluck="name",
	)
	for listing_name in listings:
		frappe.enqueue(
			"auto_parts.marketplace.sync_engine.sync_listing",
			queue="short",
			listing_name=listing_name,
		)


def import_orders_for_channel(channel_name: str) -> int:
	"""Pull and import new orders from one marketplace channel."""
	channel = frappe.db.get_value("Marketplace Channel", channel_name, ["enabled"], as_dict=True)
	if not channel or not channel.enabled:
		return 0

	connector = get_connector(channel_name)
	orders = connector.pull_orders()
	imported = 0

	for order in orders:
		try:
			if import_marketplace_order(order, channel_name):
				imported += 1
		except Exception as exc:
			write_sync_log(None, channel_name, "Inbound", "Failed", str(exc))

	return imported


def import_all_orders():
	"""Pull orders from every enabled marketplace channel."""
	if not is_sync_enabled():
		return

	for channel_name in frappe.get_all(
		"Marketplace Channel",
		filters={"enabled": 1},
		pluck="channel_name",
	):
		try:
			import_orders_for_channel(channel_name)
		except Exception:
			frappe.log_error(title=f"Marketplace order import failed for {channel_name}")


def scheduled_sync_listings():
	if is_sync_enabled():
		sync_all_listings()


def scheduled_import_orders():
	if is_sync_enabled():
		import_all_orders()


def on_stock_change(doc, method=None):
	"""Enqueue listing sync when stock changes (real-time sync)."""
	if doc.is_cancelled:
		return
	sync_listings_for_item(doc.item_code)


@frappe.whitelist()
def trigger_manual_sync(listing: str):
	return sync_listing(listing)


@frappe.whitelist()
def trigger_sync_all():
	if not is_sync_enabled():
		frappe.throw(_("Enable Marketplace Sync in Auto Parts Settings first."))
	frappe.enqueue(
		"auto_parts.marketplace.sync_engine.sync_all_listings",
		queue="long",
	)
	return True


@frappe.whitelist()
def trigger_import_orders():
	if not is_sync_enabled():
		frappe.throw(_("Enable Marketplace Sync in Auto Parts Settings first."))
	frappe.enqueue(
		"auto_parts.marketplace.sync_engine.import_all_orders",
		queue="long",
	)
	return True
