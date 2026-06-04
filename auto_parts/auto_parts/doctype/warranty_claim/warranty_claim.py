from frappe.model.document import Document


class WarrantyClaim(Document):
	def on_submit(self):
		self.db_set("status", "Submitted")
