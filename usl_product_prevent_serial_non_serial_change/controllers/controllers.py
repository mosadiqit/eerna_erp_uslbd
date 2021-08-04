# -*- coding: utf-8 -*-
# from odoo import http


# class UslProductPreventSerialNonSerialChange(http.Controller):
#     @http.route('/usl_product_prevent_serial_non_serial_change/usl_product_prevent_serial_non_serial_change/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/usl_product_prevent_serial_non_serial_change/usl_product_prevent_serial_non_serial_change/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('usl_product_prevent_serial_non_serial_change.listing', {
#             'root': '/usl_product_prevent_serial_non_serial_change/usl_product_prevent_serial_non_serial_change',
#             'objects': http.request.env['usl_product_prevent_serial_non_serial_change.usl_product_prevent_serial_non_serial_change'].search([]),
#         })

#     @http.route('/usl_product_prevent_serial_non_serial_change/usl_product_prevent_serial_non_serial_change/objects/<model("usl_product_prevent_serial_non_serial_change.usl_product_prevent_serial_non_serial_change"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('usl_product_prevent_serial_non_serial_change.object', {
#             'object': obj
#         })
