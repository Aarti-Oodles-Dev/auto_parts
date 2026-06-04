import frappe

from auto_parts.install import create_default_marketplace_channels


def execute():
	"""Convert marketplace setup: create master channel records."""
	create_default_marketplace_channels()
