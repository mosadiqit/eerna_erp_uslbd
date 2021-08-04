# -*- coding: utf-8 -*-
# from odoo import http


# class UslProductDelivery(http.Controller):
#     @http.route('/usl_product_delivery/usl_product_delivery/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/usl_product_delivery/usl_product_delivery/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('usl_product_delivery.listing', {
#             'root': '/usl_product_delivery/usl_product_delivery',
#             'objects': http.request.env['usl_product_delivery.usl_product_delivery'].search([]),
#         })

#     @http.route('/usl_product_delivery/usl_product_delivery/objects/<model("usl_product_delivery.usl_product_delivery"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('usl_product_delivery.object', {
#             'object': obj
#         })
