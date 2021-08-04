# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class usl_sales_purchase_accounting_setup(models.Model):
#     _name = 'usl_sales_purchase_accounting_setup.usl_sales_purchase_accounting_setup'
#     _description = 'usl_sales_purchase_accounting_setup.usl_sales_purchase_accounting_setup'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
