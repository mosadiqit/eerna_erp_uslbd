# -*- coding: utf-8 -*-
# from odoo import http


# class UslProductSerialCheck(http.Controller):
#     @http.route('/usl_product_serial_check/usl_product_serial_check/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/usl_product_serial_check/usl_product_serial_check/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('usl_product_serial_check.listing', {
#             'root': '/usl_product_serial_check/usl_product_serial_check',
#             'objects': http.request.env['usl_product_serial_check.usl_product_serial_check'].search([]),
#         })

#     @http.route('/usl_product_serial_check/usl_product_serial_check/objects/<model("usl_product_serial_check.usl_product_serial_check"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('usl_product_serial_check.object', {
#             'object': obj
#         })
