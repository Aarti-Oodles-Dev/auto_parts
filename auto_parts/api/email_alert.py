import frappe

def send_low_stock_alert():
    reorder_level = frappe.db.get_single_value("Auto Parts Settings", "reorder_level")
    notification = frappe.db.get_single_value("Auto Parts Settings", "low_stock_notification")

    if not reorder_level or not notification:
        return

    items = frappe.db.sql("""
        SELECT b.item_code, i.item_name, b.warehouse, b.actual_qty
        FROM `tabBin` b
        JOIN `tabItem` i ON i.name = b.item_code
        WHERE b.actual_qty <= %(reorder_level)s AND b.actual_qty > 0
    """, {"reorder_level": reorder_level}, as_dict=True)

    if not items:
        return
    
    bin_doc = frappe.get_doc("Bin", {
        "item_code": items[0]["item_code"],
        "warehouse": items[0]["warehouse"]
    })


    bin_doc.item_list = items
    bin_doc.reorder_level = reorder_level

    notification_doc = frappe.get_doc("Notification", notification)
    notification_doc.send(bin_doc)