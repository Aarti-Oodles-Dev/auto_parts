# Copyright (c) 2026, Masood Javid and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class VehicleConfiguration(Document):
	def before_save(self):
		parts = [str(self.year or ""), self.make, self.model, self.submodel, self.engine]
		self.display_name = " ".join(p for p in parts if p)
