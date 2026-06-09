import frappe
from frappe.model.document import Document

class MarketplaceSyncLog(Document):
	pass

# ---- Dashboard data methods ----

@frappe.whitelist()
def get_sync_health_summary():
    """Today ka per-channel success/failed/pending count"""
    today = frappe.utils.today()

    data = frappe.db.sql("""
        SELECT
            msl.marketplace_channel,
            msl.status,
            COUNT(*) as count
        FROM `tabMarketplace Sync Log` msl
        WHERE DATE(msl.creation) = %(today)s
        GROUP BY msl.marketplace_channel, msl.status
        ORDER BY msl.marketplace_channel, msl.status
    """, {'today': today}, as_dict=True)

    return data


@frappe.whitelist()
def get_failed_sync_trend():
    """Last 30 days daily failed count per channel"""
    from_date = frappe.utils.add_days(frappe.utils.today(), -30)

    data = frappe.db.sql("""
        SELECT
            DATE(msl.creation)      as sync_date,
            msl.marketplace_channel as channel,
            COUNT(*)                as failed_count
        FROM `tabMarketplace Sync Log` msl
        WHERE
            msl.status = 'Failed'
            AND DATE(msl.creation) >= %(from_date)s
        GROUP BY DATE(msl.creation), msl.marketplace_channel
        ORDER BY sync_date ASC
    """, {'from_date': from_date}, as_dict=True)

    return data


@frappe.whitelist()
def get_pending_listings():
    """Abhi bhi Pending status mein kitne hain"""
    data = frappe.db.sql("""
        SELECT
            msl.marketplace_channel,
            COUNT(*) as pending_count
        FROM `tabMarketplace Sync Log` msl
        WHERE msl.status = 'Pending'
        GROUP BY msl.marketplace_channel
    """, as_dict=True)

    return data