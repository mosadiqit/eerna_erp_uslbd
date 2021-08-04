# -*- coding: utf-8 -*-
# from odoo import http


# class UslProductModule(http.Controller):
#     @http.route('/usl_product_module/usl_product_module/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/usl_product_module/usl_product_module/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('usl_product_module.listing', {
#             'root': '/usl_product_module/usl_product_module',
#             'objects': http.request.env['usl_product_module.usl_product_module'].search([]),
#         })

#     @http.route('/usl_product_module/usl_product_module/objects/<model("usl_product_module.usl_product_module"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('usl_product_module.object', {
#             'object': obj
#         })
