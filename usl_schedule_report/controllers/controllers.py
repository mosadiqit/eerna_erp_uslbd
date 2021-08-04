# -*- coding: utf-8 -*-
# from odoo import http


# class CustomModule/uslScheduleReport(http.Controller):
#     @http.route('/custom_module/usl_schedule_report/custom_module/usl_schedule_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_module/usl_schedule_report/custom_module/usl_schedule_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_module/usl_schedule_report.listing', {
#             'root': '/custom_module/usl_schedule_report/custom_module/usl_schedule_report',
#             'objects': http.request.env['custom_module/usl_schedule_report.custom_module/usl_schedule_report'].search([]),
#         })

#     @http.route('/custom_module/usl_schedule_report/custom_module/usl_schedule_report/objects/<model("custom_module/usl_schedule_report.custom_module/usl_schedule_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_module/usl_schedule_report.object', {
#             'object': obj
#         })
