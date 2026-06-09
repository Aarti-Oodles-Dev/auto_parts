import frappe
from frappe.model.document import Document

class TransferDiscrepancyLog(Document):
	def before_save(self):
		self.variance_qty = (self.received_qty or 0) - (self.expected_qty or 0)

# ---- Dashboard data methods ----

@frappe.whitelist()
def get_warehouse_ops_summary():
    """Pending transfers + open discrepancies + stock value"""

    # Pending transfers
    pending = frappe.db.sql("""
        SELECT
            se.from_warehouse,
            se.to_warehouse,
            COUNT(se.name)  as transfer_count,
            SUM(sed.qty)    as total_qty
        FROM `tabStock Entry` se
        JOIN `tabStock Entry Detail` sed ON sed.parent = se.name
        WHERE
            se.stock_entry_type = 'Material Transfer'
            AND se.docstatus = 0
        GROUP BY se.from_warehouse, se.to_warehouse
        ORDER BY transfer_count DESC
    """, as_dict=True)

    # Open discrepancies
    discrepancies = frappe.db.sql("""
        SELECT
            tdl.item,
            se.from_warehouse,
            se.to_warehouse,
            tdl.expected_qty,
            tdl.received_qty,
            tdl.variance_qty,
            tdl.name as log_name
        FROM `tabTransfer Discrepancy Log` tdl
        JOIN `tabStock Entry` se ON se.name = tdl.stock_entry
        WHERE tdl.resolved = 0
        ORDER BY tdl.creation DESC
        LIMIT 50
    """, as_dict=True)

    # Stock value per warehouse
    stock_value = frappe.db.sql("""
        SELECT
            warehouse,
            SUM(stock_value)  as total_value,
            SUM(actual_qty)   as total_qty
        FROM `tabBin`
        WHERE actual_qty > 0
        GROUP BY warehouse
        ORDER BY total_value DESC
    """, as_dict=True)

    # Completed transfers last 30 days
    completed = frappe.db.sql("""
        SELECT
            DATE(se.posting_date) as transfer_date,
            COUNT(se.name)        as transfer_count
        FROM `tabStock Entry` se
        WHERE
            se.stock_entry_type = 'Material Transfer'
            AND se.docstatus = 1
            AND se.posting_date >= %(from_date)s
        GROUP BY DATE(se.posting_date)
        ORDER BY transfer_date ASC
    """, {
        'from_date': frappe.utils.add_days(frappe.utils.today(), -30)
    }, as_dict=True)

    return {
        'pending_transfers': pending,
        'discrepancies':     discrepancies,
        'stock_value':       stock_value,
        'completed_trend':   completed
    }


@frappe.whitelist()
def resolve_discrepancy(log_name):
    """Discrepancy resolve mark karo"""
    frappe.db.set_value(
        'Transfer Discrepancy Log',
        log_name,
        'resolved', 1
    )
    frappe.db.commit()
    return {'status': 'ok'}