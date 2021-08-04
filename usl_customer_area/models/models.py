# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CustomerAreaMap(models.Model):
    _inherit = "res.partner"

    customer_area = fields.Many2one(
        'customer.area.setup', string='Customer Area',required=False)

