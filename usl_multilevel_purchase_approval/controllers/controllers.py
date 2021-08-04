# -*- coding: utf-8 -*-
# from odoo import http


# class Custom/uslMultilevelPurchaseApproval(http.Controller):
#     @http.route('/custom/usl_multilevel_purchase_approval/custom/usl_multilevel_purchase_approval/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom/usl_multilevel_purchase_approval/custom/usl_multilevel_purchase_approval/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom/usl_multilevel_purchase_approval.listing', {
#             'root': '/custom/usl_multilevel_purchase_approval/custom/usl_multilevel_purchase_approval',
#             'objects': http.request.env['custom/usl_multilevel_purchase_approval.custom/usl_multilevel_purchase_approval'].search([]),
#         })

#     @http.route('/custom/usl_multilevel_purchase_approval/custom/usl_multilevel_purchase_approval/objects/<model("custom/usl_multilevel_purchase_approval.custom/usl_multilevel_purchase_approval"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom/usl_multilevel_purchase_approval.object', {
#             'object': obj
#         })
