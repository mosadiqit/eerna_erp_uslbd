# -*- coding: utf-8 -*-
# from odoo import http


# class UslCreateUserRestriction(http.Controller):
#     @http.route('/usl_restriction_setup/usl_restriction_setup/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/usl_restriction_setup/usl_restriction_setup/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('usl_restriction_setup.listing', {
#             'root': '/usl_restriction_setup/usl_restriction_setup',
#             'objects': http.request.env['usl_restriction_setup.usl_restriction_setup'].search([]),
#         })

#     @http.route('/usl_restriction_setup/usl_restriction_setup/objects/<model("usl_restriction_setup.usl_restriction_setup"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('usl_restriction_setup.object', {
#             'object': obj
#         })
