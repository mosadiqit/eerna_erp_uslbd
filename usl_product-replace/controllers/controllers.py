# -*- coding: utf-8 -*-
# from odoo import http


# class UslProduct-replace(http.Controller):
#     @http.route('/usl_product-replace/usl_product-replace/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/usl_product-replace/usl_product-replace/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('usl_product-replace.listing', {
#             'root': '/usl_product-replace/usl_product-replace',
#             'objects': http.request.env['usl_product-replace.usl_product-replace'].search([]),
#         })

#     @http.route('/usl_product-replace/usl_product-replace/objects/<model("usl_product-replace.usl_product-replace"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('usl_product-replace.object', {
#             'object': obj
#         })
