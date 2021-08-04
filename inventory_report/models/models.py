# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class inventory_report(models.Model):
#     _name = 'inventory_report.inventory_report'
#     _description = 'inventory_report.inventory_report'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
