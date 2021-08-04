# -*- coding: utf-8 -*-
# from odoo import http


# class InvoiceApprovalManagement(http.Controller):
#     @http.route('/invoice_approval_management/invoice_approval_management/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/invoice_approval_management/invoice_approval_management/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('invoice_approval_management.listing', {
#             'root': '/invoice_approval_management/invoice_approval_management',
#             'objects': http.request.env['invoice_approval_management.invoice_approval_management'].search([]),
#         })

#     @http.route('/invoice_approval_management/invoice_approval_management/objects/<model("invoice_approval_management.invoice_approval_management"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('invoice_approval_management.object', {
#             'object': obj
#         })
