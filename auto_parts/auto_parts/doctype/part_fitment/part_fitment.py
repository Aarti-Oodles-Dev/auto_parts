import frappe
from frappe import _
from frappe.model.document import Document


class PartFitment(Document):
	def validate(self):
		if not self.source:
			self.source = "Manual"

		filters = {
			"item": self.item,
			"vehicle_configuration": self.vehicle_configuration,
			"position": self.position or "",
			"qualifiers": self.qualifiers or "",
			"name": ["!=", self.name],
		}
		if frappe.db.exists("Part Fitment", filters):
			frappe.throw(
				_(
					"A fitment already exists for this Item, Vehicle Configuration, Position, and Qualifiers."
				)
			)
