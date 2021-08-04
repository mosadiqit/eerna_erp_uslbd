# -*- coding: utf-8 -*-
# from odoo import http


# class UslSaleApprovalManagement(http.Controller):
#     @http.route('/usl_sale_approval_management/usl_sale_approval_management/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/usl_sale_approval_management/usl_sale_approval_management/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('usl_sale_approval_management.listing', {
#             'root': '/usl_sale_approval_management/usl_sale_approval_management',
#             'objects': http.request.env['usl_sale_approval_management.usl_sale_approval_management'].search([]),
#         })

#     @http.route('/usl_sale_approval_management/usl_sale_approval_management/objects/<model("usl_sale_approval_management.usl_sale_approval_management"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('usl_sale_approval_management.object', {
#             'object': obj
#         })
