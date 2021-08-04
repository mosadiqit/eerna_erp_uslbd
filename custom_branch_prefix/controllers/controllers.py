# -*- coding: utf-8 -*-
# from odoo import http


# class CustomBranchPrefix(http.Controller):
#     @http.route('/custom_branch_prefix/custom_branch_prefix/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_branch_prefix/custom_branch_prefix/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_branch_prefix.listing', {
#             'root': '/custom_branch_prefix/custom_branch_prefix',
#             'objects': http.request.env['custom_branch_prefix.custom_branch_prefix'].search([]),
#         })

#     @http.route('/custom_branch_prefix/custom_branch_prefix/objects/<model("custom_branch_prefix.custom_branch_prefix"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_branch_prefix.object', {
#             'object': obj
#         })
