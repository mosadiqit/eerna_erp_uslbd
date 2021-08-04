# -*- coding: utf-8 -*-
# from odoo import http


# class UslSalesAccountingSetup(http.Controller):
#     @http.route('/usl_sales_purchase_accounting_setup/usl_sales_purchase_accounting_setup/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/usl_sales_purchase_accounting_setup/usl_sales_purchase_accounting_setup/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('usl_sales_purchase_accounting_setup.listing', {
#             'root': '/usl_sales_purchase_accounting_setup/usl_sales_purchase_accounting_setup',
#             'objects': http.request.env['usl_sales_purchase_accounting_setup.usl_sales_purchase_accounting_setup'].search([]),
#         })

#     @http.route('/usl_sales_purchase_accounting_setup/usl_sales_purchase_accounting_setup/objects/<model("usl_sales_purchase_accounting_setup.usl_sales_purchase_accounting_setup"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('usl_sales_purchase_accounting_setup.object', {
#             'object': obj
#         })
