# -*- coding: utf-8 -*-
# from odoo import http


# class UslRecivedForiginPurchased(http.Controller):
#     @http.route('/usl_recived_forigin_purchased/usl_recived_forigin_purchased/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/usl_recived_forigin_purchased/usl_recived_forigin_purchased/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('usl_recived_forigin_purchased.listing', {
#             'root': '/usl_recived_forigin_purchased/usl_recived_forigin_purchased',
#             'objects': http.request.env['usl_recived_forigin_purchased.usl_recived_forigin_purchased'].search([]),
#         })

#     @http.route('/usl_recived_forigin_purchased/usl_recived_forigin_purchased/objects/<model("usl_recived_forigin_purchased.usl_recived_forigin_purchased"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('usl_recived_forigin_purchased.object', {
#             'object': obj
#         })
