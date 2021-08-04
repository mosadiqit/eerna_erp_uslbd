# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class usl_office_food(models.Model):
#     _name = 'usl_office_food.usl_office_food'
#     _description = 'usl_office_food.usl_office_food'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
