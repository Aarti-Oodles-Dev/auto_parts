// frappe.listview_settings['Part Supersession'] = {
//     get_indicator: function(doc) {
//         if (doc.is_latest) return [__('Latest'), 'green'];
//         return [__('Superseded'), 'orange'];
//     },
//     formatters: {
//         old_item: function(val) {
//             return `<a href="/app/item/${val}">${val}</a>`;
//         },
//         new_item: function(val) {
//             return val ? `→ <a href="/app/item/${val}">${val}</a>` : '—';
//         }
//     }
// }