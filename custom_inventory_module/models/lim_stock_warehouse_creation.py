from odoo import api, fields, models
from odoo.exceptions import ValidationError

class LimStockWarehouse(models.Model):

    _inherit = 'stock.warehouse'
    _description = 'Lim(Non saleable warehouse) creation for company'

    is_non_saleable_warehouse = fields.Boolean(default=False, string="Is Non Saleable Warehouse")

    @api.model
    def create(self, vals):
        if vals['is_non_saleable_warehouse'] != False:
            count = self.env['stock.warehouse'].sudo().search_count([('is_non_saleable_warehouse','=',True)])
            if count >= 1:
                raise ValidationError("You Cannot Create more than 1 Lim Warehouse.")
        res = super(LimStockWarehouse, self).create(vals)
        return res

    def write(self, vals):
        if 'is_non_saleable_warehouse' in vals.keys():
            if vals['is_non_saleable_warehouse'] != False:
                count = self.env['stock.warehouse'].search_count([('is_non_saleable_warehouse', '=', True)])
                if count >= 1:
                    raise ValidationError("You Cannot Create more than 1 Lim Warehouse.")
        res = super().write(vals)
        return res

