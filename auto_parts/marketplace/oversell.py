# Copyright (c) 2026, Masood Javid and contributors

"""Oversell prevention — reserve stock before pushing to marketplaces."""

import math

import frappe
from erpnext.stock.utils import get_stock_balance
from frappe.utils import flt


def get_reserve_percent() -> float:
	settings = frappe.get_single("Auto Parts Settings")
	return flt(settings.default_stock_reserve_percent) or 0


def get_available_qty(
	item_code: str,
	warehouse: str | None,
	qty_buffer: int = 0,
	reserve_percent: float | None = None,
) -> int:
	"""Calculate safe quantity to publish on a marketplace."""
	if not warehouse:
		return 0

	stock = flt(get_stock_balance(item_code, warehouse))
	reserve = flt(reserve_percent) if reserve_percent is not None else get_reserve_percent()
	safe_qty = math.floor(stock * (1 - reserve / 100)) - int(qty_buffer or 0)
	return max(0, int(safe_qty))
