from frappe.model.document import Document


class ACESPIESImportBatch(Document):
	def before_save(self):
		self.total_rows = len(self.import_lines or [])

	def on_submit(self):
		self.db_set("status", "Completed")
