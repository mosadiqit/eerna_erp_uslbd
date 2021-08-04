# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class send_email_on_po_change(models.Model):
#     _name = 'send_email_on_po_change.send_email_on_po_change'
#     _description = 'send_email_on_po_change.send_email_on_po_change'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
