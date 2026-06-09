// delivery_note.js

frappe.ui.form.on('Delivery Note', {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {

            // Get Rates button
            frm.add_custom_button(__('Get Shipping Rates'), function() {
                frappe.call({
                    method: 'auto_parts.api.shipping.get_shipping_rates',
                    args: { delivery_note: frm.doc.name },
                    callback: function(r) {
                        if (r.message) {
                            let rates = r.message;
                            let msg = rates.map(rate =>
                                `${rate.carrierCode} — ${rate.serviceCode}: $${rate.shipmentCost}`
                            ).join('<br>');
                            frappe.msgprint({
                                title: __('Available Rates'),
                                message: msg,
                                indicator: 'blue'
                            });
                        }
                    }
                });
            }, __('Shipping'));

            // Create Label button
            frm.add_custom_button(__('Create Shipping Label'), function() {
                frappe.prompt([
                    {
                        label: 'Carrier Code',
                        fieldname: 'carrier_code',
                        fieldtype: 'Select',
                        options: 'ups\nfedex\nusps',
                        reqd: 1
                    },
                    {
                        label: 'Service Code',
                        fieldname: 'service_code',
                        fieldtype: 'Data',
                        reqd: 1
                    }
                ], function(values) {
                    frappe.call({
                        method: 'auto_parts.api.shipping.create_shipping_label',
                        args: {
                            delivery_note:  frm.doc.name,
                            carrier_code:   values.carrier_code,
                            service_code:   values.service_code
                        },
                        callback: function(r) {
                            if (r.message) {
                                frm.reload_doc();
                                frappe.msgprint(
                                    `Label created. Tracking: ${r.message.trackingNumber}`,
                                    'green'
                                );
                            }
                        }
                    });
                }, __('Create Label'), __('Generate'));
            }, __('Shipping'));

            // Show tracking link if exists
            if (frm.doc.custom_tracking_number) {
                frm.dashboard.add_comment(
                    `Tracking: <b>${frm.doc.custom_tracking_number}</b> 
                     via ${frm.doc.custom_carrier}`,
                    'blue', true
                );
            }
        }
    }
});