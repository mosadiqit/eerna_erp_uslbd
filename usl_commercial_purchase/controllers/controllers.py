# -*- coding: utf-8 -*-
# from odoo import http


# class UslCommercialPurchase(http.Controller):
#     @http.route('/usl_commercial_purchase/usl_commercial_purchase/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/usl_commercial_purchase/usl_commercial_purchase/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('usl_commercial_purchase.listing', {
#             'root': '/usl_commercial_purchase/usl_commercial_purchase',
#             'objects': http.request.env['usl_commercial_purchase.usl_commercial_purchase'].search([]),
#         })

#     @http.route('/usl_commercial_purchase/usl_commercial_purchase/objects/<model("usl_commercial_purchase.usl_commercial_purchase"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('usl_commercial_purchase.object', {
#             'object': obj
#         })
