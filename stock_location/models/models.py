# -*- coding: utf-8 -*-

from odoo import models, fields, api




class SaleOrderInherit(models.Model):
    _inherit = "sale.order"
    # warehouse_id  fields.Many2one(
    #     'stock.location', "Source Location New",
    #     default=get_user_location,
    #     check_company=True, readonly=True, required=True,
    #     states={'draft': [('readonly', False)]})

    @api.onchange('warehouse_id')
    def _onchange_company_id(self):
        default_warehouse = self.env.user.context_default_warehouse_id

        if default_warehouse:
            self.warehouse_id = default_warehouse
        else:
            self.warehouse_id = self.env['stock.warehouse'].search(
                [('company_id', '=', self.company_id.id)], limit=1)


    @api.model
    def _default_warehouse_id(self):
        # company = self.env.company.id
        # operatingid = self._default_operating_unit().id
        # # warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        # warehouse_ids = self.env['stock.warehouse'].search([('operating_unit_id', '=', operatingid)], limit=1)
        # return warehouse_ids
        warehouse = self.env.user.context_default_warehouse_id

        if not warehouse:
            warehouse = self.env['stock.warehouse'].search(
                [('company_id', '=', self.env.user.company_id.id)], limit=1)
        return warehouse

    # warehouse_id = fields.Many2one(
    #     'stock.warehouse', string='Warehouse DEF',
    #     required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
    #     default=_default_warehouse_id, check_company=False,delegate=False)
    print('new func')
    # vals = {}
    # print('Hiiii')
    # vals.update({"warehouse_id": 8})
    # order.update(vals)
    # location_id = fields.Many2one(
    #     'stock.location', "Source Location New",
    #     default=lambda self: self.env['res.users'].browse(
    #         # self._context.get('default_operating_unit_id')).id,
    #         self._context.get('default_operating_unit_id')).id,
    #     check_company=True, readonly=True, required=True,
    #     states={'draft': [('readonly', False)]})

    # @api.model
    # def default_get(self, fields):
    #     res = super(SaleOrderInherit, self).default_get(fields)
    #     warehouse = self.env.user.context_default_warehouse_id
    #     res['warehouse_id'] = 8
    #     res['note'] = 'warehoufdfdfdfse'
    #     res['origin'] = '5334fff'
    #     res['fiscal_position_id'] = 2
    #     res['pricelist_id'] = 2
    #     res['l10n_in_journal_id'] = 17
    #     # res['user_id'] = 820
    #     res['medium_id'] = 2
    #     # res['picking_policy'] = 'direct'
    #     return res


