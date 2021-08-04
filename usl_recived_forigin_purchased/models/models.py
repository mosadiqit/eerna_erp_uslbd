# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class usl_recived_forigin_purchased(models.Model):
#     _name = 'usl_recived_forigin_purchased.usl_recived_forigin_purchased'
#     _description = 'usl_recived_forigin_purchased.usl_recived_forigin_purchased'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
