# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class usl_salesman_route(models.Model):
#     _name = 'usl_salesman_route.usl_salesman_route'
#     _description = 'usl_salesman_route.usl_salesman_route'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
