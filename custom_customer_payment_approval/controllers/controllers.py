# -*- coding: utf-8 -*-
# from odoo import http


# class CustomCustomerPaymentApproval(http.Controller):
#     @http.route('/custom_customer_payment_approval/custom_customer_payment_approval/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_customer_payment_approval/custom_customer_payment_approval/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_customer_payment_approval.listing', {
#             'root': '/custom_customer_payment_approval/custom_customer_payment_approval',
#             'objects': http.request.env['custom_customer_payment_approval.custom_customer_payment_approval'].search([]),
#         })

#     @http.route('/custom_customer_payment_approval/custom_customer_payment_approval/objects/<model("custom_customer_payment_approval.custom_customer_payment_approval"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_customer_payment_approval.object', {
#             'object': obj
#         })
