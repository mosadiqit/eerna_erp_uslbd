from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _default_warehouse_id(self):
        warehouse = self.env.user.context_default_warehouse_id
        if not warehouse:
            warehouse = self.env['stock.warehouse'].search(
                [('company_id', '=', self.env.user.company_id.id)], limit=1)
        return warehouse

    warehouse_id = fields.Many2one(default=_default_warehouse_id)


    def _onchange_company_id(self):
        default_warehouse = self.env.user.context_default_warehouse_id

        if default_warehouse:
            self.warehouse_id = default_warehouse
        else:
            self.warehouse_id = self.env['stock.warehouse'].search(
                [('company_id', '=', self.company_id.id)])

