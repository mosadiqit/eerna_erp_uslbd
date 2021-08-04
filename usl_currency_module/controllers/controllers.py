# -*- coding: utf-8 -*-
# from odoo import http


# class UslCurrencyModule(http.Controller):
#     @http.route('/usl_currency_module/usl_currency_module/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/usl_currency_module/usl_currency_module/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('usl_currency_module.listing', {
#             'root': '/usl_currency_module/usl_currency_module',
#             'objects': http.request.env['usl_currency_module.usl_currency_module'].search([]),
#         })

#     @http.route('/usl_currency_module/usl_currency_module/objects/<model("usl_currency_module.usl_currency_module"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('usl_currency_module.object', {
#             'object': obj
#         })
