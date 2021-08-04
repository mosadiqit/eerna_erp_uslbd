# -*- coding: utf-8 -*-
# from odoo import http


# class SaleExtraCost(http.Controller):
#     @http.route('/sale_extra_cost/sale_extra_cost/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_extra_cost/sale_extra_cost/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_extra_cost.listing', {
#             'root': '/sale_extra_cost/sale_extra_cost',
#             'objects': http.request.env['sale_extra_cost.sale_extra_cost'].search([]),
#         })

#     @http.route('/sale_extra_cost/sale_extra_cost/objects/<model("sale_extra_cost.sale_extra_cost"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_extra_cost.object', {
#             'object': obj
#         })
