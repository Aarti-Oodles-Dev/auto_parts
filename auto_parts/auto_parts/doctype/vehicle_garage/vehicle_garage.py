# Copyright (c) 2026, Masood Javid and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class VehicleGarage(Document):
	def validate(self):
		if self.vin:
			self.vin = self.vin.strip().upper()

	def before_save(self):
		if self.vehicle_configuration and not self.make:
			vehicle = frappe.get_doc("Vehicle Configuration", self.vehicle_configuration)
			self.year = vehicle.year
			self.make = vehicle.make
			self.model = vehicle.model
			self.engine = vehicle.engine
