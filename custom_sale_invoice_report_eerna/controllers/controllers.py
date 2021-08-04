# -*- coding: utf-8 -*-
# from odoo import http


# class CustomSaleInvoiceReportEerna(http.Controller):
#     @http.route('/custom_sale_invoice_report_eerna/custom_sale_invoice_report_eerna/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_sale_invoice_report_eerna/custom_sale_invoice_report_eerna/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_sale_invoice_report_eerna.listing', {
#             'root': '/custom_sale_invoice_report_eerna/custom_sale_invoice_report_eerna',
#             'objects': http.request.env['custom_sale_invoice_report_eerna.custom_sale_invoice_report_eerna'].search([]),
#         })

#     @http.route('/custom_sale_invoice_report_eerna/custom_sale_invoice_report_eerna/objects/<model("custom_sale_invoice_report_eerna.custom_sale_invoice_report_eerna"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_sale_invoice_report_eerna.object', {
#             'object': obj
#         })
