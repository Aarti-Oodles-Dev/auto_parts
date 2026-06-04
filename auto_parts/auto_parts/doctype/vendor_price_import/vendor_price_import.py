from frappe.model.document import Document


class VendorPriceImport(Document):
	def on_submit(self):
		self.db_set("status", "Completed")
