# -*- coding: utf-8 -*-
# from odoo import http


# class ProductAccessRight(http.Controller):
#     @http.route('/product_access_right/product_access_right/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/product_access_right/product_access_right/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('product_access_right.listing', {
#             'root': '/product_access_right/product_access_right',
#             'objects': http.request.env['product_access_right.product_access_right'].search([]),
#         })

#     @http.route('/product_access_right/product_access_right/objects/<model("product_access_right.product_access_right"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('product_access_right.object', {
#             'object': obj
#         })
