from odoo import api, fields, models


class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    transport_nature_no = fields.Char("Transport Nature & No.")
