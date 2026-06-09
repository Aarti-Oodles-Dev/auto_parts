from frappe.model.document import Document
import frappe

class RMA(Document):
    def on_submit(self):
        self.db_set("status", "Approved")
        self.create_return_delivery_note()

    def create_return_delivery_note(self):
        dn = frappe.new_doc('Delivery Note')
        dn.customer = self.customer
        dn.is_return = 1
        dn.custom_rma = self.name
        dn.posting_date = frappe.utils.today()

        for item in self.items:
            dn.append('items', {
                'item_code': item.item_code,
                'qty': item.qty,
                'warehouse': item.warehouse,
                'against_sales_invoice': item.sales_invoice,
                'batch_no': item.batch_no or ''
            })

        dn.flags.ignore_permissions = True
        dn.insert()
        dn.submit()

        frappe.msgprint(
            f'Return Delivery Note <b>{dn.name}</b> created.',
            indicator='green'
        )

        self.db_set('return_dn', dn.name)