# Copyright (c) 2026, Masood Javid and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from auto_parts.vin.decode import normalize_vin, validate_vin


class VehicleGarage(Document):
	def validate(self):
		if self.vin:
			self.vin = normalize_vin(self.vin)
			validate_vin(self.vin)

	def before_save(self):
		if self.vehicle_configuration and not self.make:
			vehicle = frappe.get_doc("Vehicle Configuration", self.vehicle_configuration)
			self.year = vehicle.year
			self.make = vehicle.make
			self.model = vehicle.model
			self.engine = vehicle.engine
