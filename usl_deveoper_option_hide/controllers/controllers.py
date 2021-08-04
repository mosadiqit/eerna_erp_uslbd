# -*- coding: utf-8 -*-
# from odoo import http


# class CustomModule/uslDeveoperOptionHide(http.Controller):
#     @http.route('/custom_module/usl_deveoper_option_hide/custom_module/usl_deveoper_option_hide/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_module/usl_deveoper_option_hide/custom_module/usl_deveoper_option_hide/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_module/usl_deveoper_option_hide.listing', {
#             'root': '/custom_module/usl_deveoper_option_hide/custom_module/usl_deveoper_option_hide',
#             'objects': http.request.env['custom_module/usl_deveoper_option_hide.custom_module/usl_deveoper_option_hide'].search([]),
#         })

#     @http.route('/custom_module/usl_deveoper_option_hide/custom_module/usl_deveoper_option_hide/objects/<model("custom_module/usl_deveoper_option_hide.custom_module/usl_deveoper_option_hide"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_module/usl_deveoper_option_hide.object', {
#             'object': obj
#         })
