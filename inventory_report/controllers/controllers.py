# -*- coding: utf-8 -*-
# from odoo import http


# class InventoryReport(http.Controller):
#     @http.route('/inventory_report/inventory_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/inventory_report/inventory_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('inventory_report.listing', {
#             'root': '/inventory_report/inventory_report',
#             'objects': http.request.env['inventory_report.inventory_report'].search([]),
#         })

#     @http.route('/inventory_report/inventory_report/objects/<model("inventory_report.inventory_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('inventory_report.object', {
#             'object': obj
#         })
