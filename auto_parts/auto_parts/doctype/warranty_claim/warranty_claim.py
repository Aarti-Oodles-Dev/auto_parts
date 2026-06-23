from frappe.model.document import Document
import frappe

class WarrantyClaim(Document):
    def on_submit(self):
        self.db_set("status", "Submitted")
        if self.workflow_state == 'Approved':
            self.create_credit_note()

    def create_credit_note(self):
        # Original SI ke items fetch karo — item_code se match karke row ID lo
        original_si_items = {
            d.item_code: d.name
            for d in frappe.get_doc('Sales Invoice', self.sales_invoice).items
        }

        si = frappe.new_doc('Sales Invoice')
        si.customer = self.customer
        si.is_return = 1
        si.return_against = self.sales_invoice
        si.custom_warranty_claim = self.name
        si.posting_date = frappe.utils.today()

        for item in self.items:
            si.append('items', {
                'item_code': item.item,
                'qty': -1 * item.qty,
                'sales_invoice_item': original_si_items.get(item.item)  # original SI row ID
            })

        si.flags.ignore_permissions = True
        si.insert()
        si.submit()

        frappe.msgprint(
            f'Credit Note <b>{si.name}</b> created.',
            indicator='green'
        )