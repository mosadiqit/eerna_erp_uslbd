# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class custom_module/usl_ci_wise_landed_cost(models.Model):
#     _name = 'custom_module/usl_ci_wise_landed_cost.custom_module/usl_ci_wise_landed_cost'
#     _description = 'custom_module/usl_ci_wise_landed_cost.custom_module/usl_ci_wise_landed_cost'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
