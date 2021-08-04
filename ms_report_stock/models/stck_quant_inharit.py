import datetime

from odoo import fields, models, api


class StockQuantInherit(models.Model):
    _inherit = 'stock.quant'
    _description = 'Description'

    def create(self, vals):
        print(self)
        print(vals)
        return super(StockQuantInherit, self).create(vals)

    def write(self, vals):
        print(self)
        print(vals)
        if 'in_date' in vals.keys():
            vals['in_date'] = datetime.datetime.now()
        return super(StockQuantInherit, self).write(vals)
