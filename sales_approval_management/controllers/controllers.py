# -*- coding: utf-8 -*-
# from odoo import http


# class SalesApprovalManagement(http.Controller):
#     @http.route('/sales_approval_management/sales_approval_management/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sales_approval_management/sales_approval_management/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sales_approval_management.listing', {
#             'root': '/sales_approval_management/sales_approval_management',
#             'objects': http.request.env['sales_approval_management.sales_approval_management'].search([]),
#         })

#     @http.route('/sales_approval_management/sales_approval_management/objects/<model("sales_approval_management.sales_approval_management"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sales_approval_management.object', {
#             'object': obj
#         })

import requests

# url = "http://10.200.2.68:8069/api/sale.order"
#
# payload = """{
#    "limit": 2,
#    "fields": "['id', 'partner_id', 'name']",
#    "domain": "[('id', 'in', [10,11,12,13,14])]",
#    "offset": 0
#   }"""
#
# headers = {
#     'access-token': "access_token_474897e3a8fd24c529cb6361ca162ab5e3177801",
#     'content-type': "application/json"
#     }
#
# response = requests.request("GET", url, data=payload, headers=headers)

# print(response.text)

# url = "http://10.200.2.68:8069/api/auth/token"
#
# payload = {
#   "db": "HRTestDB",
#   "login": "mostofa.zaman@uslbd.com",
#   "password": "Smart1@3"
# }
#
# headers = {
#     'content-type': "text/plain",
#     # 'access-token': "access_token_ebb1914bbdb5622cd782a1a0ff51f81a2cba042a"
#     }
#
# response = requests.request("GET", url, data=payload, headers=headers)
#
# print(response.text)
