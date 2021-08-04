# -*- coding: utf-8 -*-
# from odoo import http


# class CustomeSaleProduct(http.Controller):
#     @http.route('/custom_stock_move_inline/custom_stock_move_inline/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_stock_move_inline/custom_stock_move_inline/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_stock_move_inline.listing', {
#             'root': '/custom_stock_move_inline/custom_stock_move_inline',
#             'objects': http.request.env['custom_stock_move_inline.custom_stock_move_inline'].search([]),
#         })

#     @http.route('/custom_stock_move_inline/custom_stock_move_inline/objects/<model("custom_stock_move_inline.custom_stock_move_inline"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_stock_move_inline.object', {
#             'object': obj
#         })

# from odoo import http
# # from odoo.addons.stock.controllers.main import StockReportController
# from odoo.http import request
#
# class products(http.Controller):
#
#     @http.route('/allProducts',type='json',auth='user')
#     def getProducts(self):
#         pro=request.env['product.product'].search([])
#         products=[]



