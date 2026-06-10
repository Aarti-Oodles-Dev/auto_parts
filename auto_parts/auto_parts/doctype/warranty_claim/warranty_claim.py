from frappe.model.document import Document
import frappe

class WarrantyClaim(Document):
    def on_submit(self):
        self.db_set("status", "Submitted")
        if self.workflow_state == 'Approved':
            self.create_credit_note()

    def create_credit_note(self):
        si = frappe.new_doc('Sales Invoice')
        si.customer = self.customer
        si.is_return = 1
        si.custom_warranty_claim = self.name
        si.posting_date = frappe.utils.today()

        for item in self.items:
            si.append('items', {
                'item_code': item.item,
                'qty': -1 * item.qty,
            })

        si.flags.ignore_permissions = True
        si.insert()
        si.submit()

        self.db_set('sales_invoice', si.name)

        frappe.msgprint(
            f'Credit Note <b>{si.name}</b> created.',
            indicator='green'
        )