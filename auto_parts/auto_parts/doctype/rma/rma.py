from frappe.model.document import Document


class RMA(Document):
	def on_submit(self):
		self.db_set("status", "Approved")
