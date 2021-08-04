# -*- coding: utf-8 -*-
# from odoo import http


# class CustomModule/uslLcManagement(http.Controller):
#     @http.route('/custom_module/usl_lc_management/custom_module/usl_lc_management/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_module/usl_lc_management/custom_module/usl_lc_management/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_module/usl_lc_management.listing', {
#             'root': '/custom_module/usl_lc_management/custom_module/usl_lc_management',
#             'objects': http.request.env['custom_module/usl_lc_management.custom_module/usl_lc_management'].search([]),
#         })

#     @http.route('/custom_module/usl_lc_management/custom_module/usl_lc_management/objects/<model("custom_module/usl_lc_management.custom_module/usl_lc_management"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_module/usl_lc_management.object', {
#             'object': obj
#         })
