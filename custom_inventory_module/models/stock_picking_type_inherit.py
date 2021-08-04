from odoo import api, fields, models, _


class StockPickingTypeInherit(models.Model):
    _inherit = 'stock.picking.type'


    is_warehouse_return = fields.Boolean(string="Is Return Type?", default=False)
