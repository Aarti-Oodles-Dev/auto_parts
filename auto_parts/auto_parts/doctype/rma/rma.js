frappe.ui.form.on('RMA', {
    delivery_note(frm) {
        frm.trigger('fetch_dn_items');
    },

    fetch_dn_items(frm) {
        if (!frm.doc.delivery_note) {
            frm.clear_table('items');
            frm.refresh_field('items');
            return;
        }

        frappe.db.get_doc('Delivery Note', frm.doc.delivery_note).then(dn => {
            frm.clear_table('items');

            dn.items.forEach(row => {
                let child = frm.add_child('items');
                child.item = row.item_code;
                child.qty = row.qty;
                child.delivery_note_item = row.name; // original DN row ID
            });

            frm.refresh_field('items');
        });
    }
});