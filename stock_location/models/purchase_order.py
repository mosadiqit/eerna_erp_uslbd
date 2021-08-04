# -*- coding: utf-8 -*-
# © 2020 Unisoft Systems Limited (http://www.uslbd.com)
# @author Mostofa Zaman <mostofa.zaman@uslbd.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    @api.onchange('picking_type_id')
    def _get_default_picking_type_id(self):
        User = self.env['res.users']
        branch = User.search([('id', '=', self.env.user.id)])
        branchs_ids = list()
        for br in branch.branch_ids:
            branchs_ids.append(br.id)

        warehouse_id = self.env['stock.warehouse'].sudo().search(
            [('branch_id', 'in', branchs_ids)])
        return {'domain': {'picking_type_id': [('warehouse_id', 'in', warehouse_id.ids), ('sequence_code', '=', "IN")]}}

    @api.onchange('branch_id')
    def _onchange_picking_type_id(self):

        if self.branch_id != self.env.user.branch_id:
            warehouse = self.env['stock.warehouse'].search(
                [('branch_id', '=', self.branch_id.id)], limit=1)
            picking_type_id = self.env['stock.picking.type'].search(
                [('warehouse_id', '=', warehouse.id), ('sequence_code', '=', "IN")], limit=1)
            self.picking_type_id = picking_type_id.id
        else:
            print('come in else ')
            default_warehouse = self.env.user.context_default_warehouse_id

            if default_warehouse:
                picking_type_id = self.env['stock.picking.type'].search(
                    [('warehouse_id', '=', default_warehouse.id), ('sequence_code', '=', "IN")], limit=1)
                self.picking_type_id = picking_type_id.id

    # def _default_picking_type(self):
    #     default_warehouse = self.env.user.context_default_warehouse_id
    #     print(' called method', default_warehouse.name)
    #
    #     if default_warehouse:
    #         picking_type_id = self.env['stock.picking.type'].search(
    #             [('warehouse_id', '=', default_warehouse.id), ('sequence_code', '=', "IN")], limit=1)
    #         print('picking type id and name', picking_type_id.id, picking_type_id.name)
    #         self.picking_type_id = picking_type_id.id
    #
    #         # lambda self: self._default_picking_type()
    #
    # picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To',
    #                                   required=True, default=25,
    #                                   help="This willsss determine operation type of incoming shipment")
