# -*- coding: utf-8 -*-
# from odoo import http


# class CustomModule/uslCompanyWiseSalesPrice(http.Controller):
#     @http.route('/custom_module/usl_company_wise_sales_price/custom_module/usl_company_wise_sales_price/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_module/usl_company_wise_sales_price/custom_module/usl_company_wise_sales_price/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_module/usl_company_wise_sales_price.listing', {
#             'root': '/custom_module/usl_company_wise_sales_price/custom_module/usl_company_wise_sales_price',
#             'objects': http.request.env['custom_module/usl_company_wise_sales_price.custom_module/usl_company_wise_sales_price'].search([]),
#         })

#     @http.route('/custom_module/usl_company_wise_sales_price/custom_module/usl_company_wise_sales_price/objects/<model("custom_module/usl_company_wise_sales_price.custom_module/usl_company_wise_sales_price"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_module/usl_company_wise_sales_price.object', {
#             'object': obj
#         })
