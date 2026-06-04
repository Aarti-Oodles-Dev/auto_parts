from frappe.model.document import Document


class VINDecodeCache(Document):
	def before_save(self):
		if self.vin:
			self.vin = self.vin.strip().upper()
