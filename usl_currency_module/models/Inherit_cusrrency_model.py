from odoo import fields, models


class CurrencyModelInherit(models.Model):
    _inherit="res.currency"

    local_currency=fields.Float(string="Local Currency")