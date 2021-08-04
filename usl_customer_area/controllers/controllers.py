# -*- coding: utf-8 -*-
# from odoo import http


# class UslCustomerArea(http.Controller):
#     @http.route('/usl_customer_area/usl_customer_area/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/usl_customer_area/usl_customer_area/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('usl_customer_area.listing', {
#             'root': '/usl_customer_area/usl_customer_area',
#             'objects': http.request.env['usl_customer_area.usl_customer_area'].search([]),
#         })

#     @http.route('/usl_customer_area/usl_customer_area/objects/<model("usl_customer_area.usl_customer_area"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('usl_customer_area.object', {
#             'object': obj
#         })
