import frappe
from frappe import _
from frappe.model.document import Document


class PartSupersession(Document):
	def validate(self):
		if self.old_item == self.new_item:
			frappe.throw(_("Old Item and New Item cannot be the same"))
