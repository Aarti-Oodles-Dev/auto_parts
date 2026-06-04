from frappe.model.document import Document


class TransferDiscrepancyLog(Document):
	def before_save(self):
		self.variance_qty = (self.received_qty or 0) - (self.expected_qty or 0)
