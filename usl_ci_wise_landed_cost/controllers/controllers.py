# -*- coding: utf-8 -*-
# from odoo import http


# class CustomModule/uslCiWiseLandedCost(http.Controller):
#     @http.route('/custom_module/usl_ci_wise_landed_cost/custom_module/usl_ci_wise_landed_cost/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_module/usl_ci_wise_landed_cost/custom_module/usl_ci_wise_landed_cost/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_module/usl_ci_wise_landed_cost.listing', {
#             'root': '/custom_module/usl_ci_wise_landed_cost/custom_module/usl_ci_wise_landed_cost',
#             'objects': http.request.env['custom_module/usl_ci_wise_landed_cost.custom_module/usl_ci_wise_landed_cost'].search([]),
#         })

#     @http.route('/custom_module/usl_ci_wise_landed_cost/custom_module/usl_ci_wise_landed_cost/objects/<model("custom_module/usl_ci_wise_landed_cost.custom_module/usl_ci_wise_landed_cost"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_module/usl_ci_wise_landed_cost.object', {
#             'object': obj
#         })
