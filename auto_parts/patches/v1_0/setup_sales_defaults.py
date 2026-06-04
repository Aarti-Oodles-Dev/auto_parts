# Copyright (c) 2026, Masood Javid and contributors

from auto_parts.install import create_default_pos_profile, create_default_price_lists


def execute():
	create_default_price_lists()
	create_default_pos_profile()
