import frappe
from frappe import _
from frappe.model.document import Document


class PartSupersession(Document):
	def validate(self):
		if self.old_item == self.new_item:
			frappe.throw(_("Old Item and New Item cannot be the same"))

@frappe.whitelist()
def get_supersession_chain(item_code):
    chain = [item_code]
    current = item_code
    
    for _ in range(20):  # max depth safeguard
        nxt = frappe.db.get_value(
            'Part Supersession',
            {'old_item': current},
            'new_item'
        )
        if not nxt or nxt in chain:
            break
        chain.append(nxt)
        current = nxt
    
    return chaingfhghg