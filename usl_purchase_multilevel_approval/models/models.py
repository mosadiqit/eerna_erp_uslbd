# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class custom/usl_multilevel_purchase_approval(models.Model):
#     _name = 'custom/usl_multilevel_purchase_approval.custom/usl_multilevel_purchase_approval'
#     _description = 'custom/usl_multilevel_purchase_approval.custom/usl_multilevel_purchase_approval'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
