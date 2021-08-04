from odoo import api, fields, models, _, tools

from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class StockLandedCostInherit(models.Model):
    # _name = 's'
    # _rec_name = 'name'
    # _description = 'New Description'
    _name= "stock.landed.cost.inherit"
    _inherit = 'stock.landed.cost'

    transfer_foreign = fields.Many2one('stock.picking',string="Transfer")