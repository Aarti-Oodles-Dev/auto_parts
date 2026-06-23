from frappe.model.document import Document
import frappe

class RMA(Document):
    def on_submit(self):
        self.db_set("status", "Approved")
        self.create_return_delivery_note()

    def create_return_delivery_note(self):
        original_dn_items = {
            d.item_code: d.name
            for d in frappe.get_doc('Delivery Note', self.delivery_note).items
        }

        dn = frappe.new_doc('Delivery Note')
        dn.customer = self.customer
        dn.is_return = 1
        dn.return_against = self.delivery_note
        dn.custom_rma = self.name
        dn.posting_date = frappe.utils.today()

        for item in self.items:
            dn.append('items', {
                'item_code': item.item,
                'qty': -item.qty,
                'warehouse': item.return_warehouse,
                'dn_detail': original_dn_items.get(item.item),  # against_dn_item nahi, dn_detail hai
            })

        dn.flags.ignore_permissions = True
        dn.insert()
        dn.submit()

        frappe.msgprint(
            f'Return Delivery Note <b>{dn.name}</b> created.',
            indicator='green'
        )

        self.db_set('return_dn', dn.name)