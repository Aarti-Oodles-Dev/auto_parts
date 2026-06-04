from frappe.model.document import Document


class CoreReturn(Document):
	def on_submit(self):
		self.db_set("status", "Received")
