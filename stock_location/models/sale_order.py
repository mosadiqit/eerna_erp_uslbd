# -*- coding: utf-8 -*-
# © 2020 Unisoft Systems Limited (http://www.uslbd.com)
# @author Mostofa Zaman <mostofa.zaman@uslbd.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    @api.onchange('warehouse_id')
    def _onchange_company_id(self):
        default_warehouse = self.env.user.context_default_warehouse_id

        if default_warehouse:
            self.warehouse_id = default_warehouse
        else:
            self.warehouse_id = self.env['stock.warehouse'].search(
                [('company_id', '=', self.company_id.id)], limit=1)
