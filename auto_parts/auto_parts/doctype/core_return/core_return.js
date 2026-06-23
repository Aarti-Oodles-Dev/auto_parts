frappe.ui.form.on('Core Return', {
    sales_invoice(frm) {
        frm.trigger('fetch_si_items');
    },

    fetch_si_items(frm) {
        if (!frm.doc.sales_invoice) {
            frm.clear_table('items');
            frm.refresh_field('items');
            return;
        }

        frappe.db.get_doc('Sales Invoice', frm.doc.sales_invoice).then(si => {
            frm.clear_table('items');

            si.items.forEach(row => {
                let child = frm.add_child('items');
                child.item = row.item_code;
                child.core_qty = row.qty;
                child.sales_invoice_item = row.name; // original SI row ID
            });

            frm.refresh_field('items');
        });
    }
});