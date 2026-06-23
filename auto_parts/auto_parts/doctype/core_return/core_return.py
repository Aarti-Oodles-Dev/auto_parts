from frappe.model.document import Document
import frappe

class CoreReturn(Document):
	def on_submit(self):
		self.db_set("status", "Received")
		self.create_stock_entry()

	def create_stock_entry(self):
		se = frappe.new_doc('Stock Entry')
		se.stock_entry_type = 'Material Transfer'
		se.posting_date = self.posting_date
		se.custom_core_return = self.name  # custom field hoga SE pe — agar nahi hai toh hata do

		for item in self.items:
			se.append('items', {
				'item_code': item.item,
				'qty': item.core_qty,
				"basic_rate": item.core_charge,
				's_warehouse': item.source_warehouse,
				't_warehouse': item.target_warehouse,
			})

		se.flags.ignore_permissions = True
		se.insert()
		se.submit()

		frappe.msgprint(
			f'Stock Entry <b>{se.name}</b> created.',
			indicator='green'
		)