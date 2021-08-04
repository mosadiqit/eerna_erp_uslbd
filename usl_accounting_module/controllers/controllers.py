# -*- coding: utf-8 -*-
# from odoo import http


# class UslAccountingModule(http.Controller):
#     @http.route('/usl_accounting_module/usl_accounting_module/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/usl_accounting_module/usl_accounting_module/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('usl_accounting_module.listing', {
#             'root': '/usl_accounting_module/usl_accounting_module',
#             'objects': http.request.env['usl_accounting_module.usl_accounting_module'].search([]),
#         })

#     @http.route('/usl_accounting_module/usl_accounting_module/objects/<model("usl_accounting_module.usl_accounting_module"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('usl_accounting_module.object', {
#             'object': obj
#         })
