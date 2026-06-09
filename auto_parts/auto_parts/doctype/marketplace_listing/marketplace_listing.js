frappe.ui.form.on('Marketplace Listing', {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Sync Now'), function() {
                frappe.call({
                    method: 'auto_parts.auto_parts.doctype.marketplace_sync_log.marketplace_sync_log.trigger_manual_sync',
                    args: { listing: frm.doc.name },
                    callback: function(r) {
                        frappe.show_alert({
                            message: 'Sync triggered',
                            indicator: 'green'
                        });
                    }
                });
            }, __('Marketplace'));
        }
    },
    channel_markup_percent: function(frm) {
        if (frm.doc.pricing_method === 'Cost Plus') {
            frm.call('calculate_channel_price').then(() => {
                frm.refresh_field('listing_price');
            });
        }
    }
});
