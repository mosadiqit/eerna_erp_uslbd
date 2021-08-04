# -*- coding: utf-8 -*-
# from odoo import http


# class CustomModule/uslRecurringInvoice(http.Controller):
#     @http.route('/custom_module/usl_recurring_invoice/custom_module/usl_recurring_invoice/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_module/usl_recurring_invoice/custom_module/usl_recurring_invoice/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_module/usl_recurring_invoice.listing', {
#             'root': '/custom_module/usl_recurring_invoice/custom_module/usl_recurring_invoice',
#             'objects': http.request.env['custom_module/usl_recurring_invoice.custom_module/usl_recurring_invoice'].search([]),
#         })

#     @http.route('/custom_module/usl_recurring_invoice/custom_module/usl_recurring_invoice/objects/<model("custom_module/usl_recurring_invoice.custom_module/usl_recurring_invoice"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_module/usl_recurring_invoice.object', {
#             'object': obj
#         })
