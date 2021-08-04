# -*- coding: utf-8 -*-
# from odoo import http


# class UslForignPurchaseDashboard(http.Controller):
#     @http.route('/usl_forign_purchase_dashboard/usl_forign_purchase_dashboard/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/usl_forign_purchase_dashboard/usl_forign_purchase_dashboard/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('usl_forign_purchase_dashboard.listing', {
#             'root': '/usl_forign_purchase_dashboard/usl_forign_purchase_dashboard',
#             'objects': http.request.env['usl_forign_purchase_dashboard.usl_forign_purchase_dashboard'].search([]),
#         })

#     @http.route('/usl_forign_purchase_dashboard/usl_forign_purchase_dashboard/objects/<model("usl_forign_purchase_dashboard.usl_forign_purchase_dashboard"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('usl_forign_purchase_dashboard.object', {
#             'object': obj
#         })
