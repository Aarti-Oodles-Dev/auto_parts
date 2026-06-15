import frappe
from frappe.utils import add_days, nowdate

def execute(filters=None):
    columns = [
        {"label": "Item Code",             "fieldname": "item_code",       "fieldtype": "Link",     "options": "Item",  "width": 150},
        {"label": "Item Name",             "fieldname": "item_name",       "fieldtype": "Data",                         "width": 200},
        {"label": "Warehouse",             "fieldname": "warehouse",       "fieldtype": "Link",     "options": "Warehouse", "width": 150},
        {"label": "Avg Daily Sales (30d)", "fieldname": "avg_daily_sales", "fieldtype": "Float",                        "width": 150},
        {"label": "Current Stock",         "fieldname": "actual_qty",      "fieldtype": "Float",                        "width": 120},
        {"label": "Days of Stock Left",    "fieldname": "days_left",       "fieldtype": "Int",                          "width": 130},
        {"label": "Suggested Reorder Qty", "fieldname": "suggested_qty",   "fieldtype": "Float",                        "width": 160},
        {"label": "Status",                "fieldname": "status",          "fieldtype": "Data",                         "width": 120},
    ]

    # Last 30 days sales velocity per item per warehouse
    sales_data = frappe.db.sql("""
        SELECT
            sii.item_code,
            sii.item_name,
            sii.warehouse,
            SUM(sii.qty) / 30.0 AS avg_daily_sales
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE si.docstatus = 1
          AND si.posting_date >= %(from_date)s
          AND si.posting_date <= %(to_date)s
        GROUP BY sii.item_code, sii.warehouse
    """, {
        "from_date": add_days(nowdate(), -30),
        "to_date": nowdate()
    }, as_dict=True)

    data = []
    for row in sales_data:
        actual_qty = frappe.db.get_value(
            "Bin",
            {"item_code": row.item_code, "warehouse": row.warehouse},
            "actual_qty"
        ) or 0

        avg = row.avg_daily_sales or 0
        days_left = int(actual_qty / avg) if avg > 0 else 9999

        # 30 din cover karne ke liye kitna chahiye minus jo hai
        suggested_qty = round(max((avg * 30) - actual_qty, 0), 2)

        if days_left <= 7:
            status = "🔴 Critical"
        elif days_left <= 14:
            status = "🟡 Low"
        else:
            status = "🟢 Adequate"

        data.append({
            "item_code":       row.item_code,
            "item_name":       row.item_name,
            "warehouse":       row.warehouse,
            "avg_daily_sales": round(avg, 3),
            "actual_qty":      actual_qty,
            "days_left":       days_left if days_left != 9999 else 0,
            "suggested_qty":   suggested_qty,
            "status":          status,
        })

    # Critical items pehle
    data.sort(key=lambda x: x["days_left"])
    return columns, data