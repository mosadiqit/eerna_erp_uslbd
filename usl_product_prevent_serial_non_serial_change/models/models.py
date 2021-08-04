# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class usl_product_prevent_serial_non_serial_change(models.Model):
#     _name = 'usl_product_prevent_serial_non_serial_change.usl_product_prevent_serial_non_serial_change'
#     _description = 'usl_product_prevent_serial_non_serial_change.usl_product_prevent_serial_non_serial_change'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
