from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv.osv import osv
from odoo.tools.float_utils import float_compare, float_is_zero, float_round



class StockPickingInharit(models.Model):
    _inherit = 'stock.picking'

    @api.onchange('commercial_invoice')
    def onchange_commercial_invoice(self):
        if self.commercial_invoice:
            move_id = self.env['account.move'].search([('id','=',self.commercial_invoice.id)])
            move_line_id = self.env['account.move.line'].search([('move_id','=',move_id.id),('account_internal_type','=','other')])
            for rec in self:
                lines = list()
                for line in move_line_id:
                    vals = {
                        'product_id':line.product_id.id,
                        'branch_id':self.env.user.branch_id.id,
                        'product_uom_qty':line.quantity,
                        'reserved_availability':0,
                        'quantity_done':0,
                        'name':line.name,
                        'product_uom':line.product_id.uom_id.id
                    }
                    lines.append((0,0,vals))
                rec.move_ids_without_package = lines


            print('Hello')


    def button_validate(self):
        self.ensure_one()
        if not self.move_lines and not self.move_line_ids:
            raise UserError(_('Please add some items to move.'))

        # Clean-up the context key at validation to avoid forcing the creation of immediate
        # transfers.
        # for rec in self.move_line_ids_without_package.lot_id:
        #     stock_reserved_check = self.env['stock.quant'].search([('lot_id','=',rec.id),('location_id','=',self.location_id.id)])
        #     if stock_reserved_check.reserved_quantity == 0:
        #         print(rec)

        ctx = dict(self.env.context)
        ctx.pop('default_immediate_transfer', None)
        self = self.with_context(ctx)

        # add user as a follower
        self.message_subscribe([self.env.user.partner_id.id])

        # If no lots when needed, raise error
        picking_type = self.picking_type_id
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in self.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
        no_reserved_quantities = all(float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in self.move_line_ids)
        if no_reserved_quantities and no_quantities_done:
            raise UserError(_('You cannot validate a transfer if no quantites are reserved nor done. To force the transfer, switch in edit more and encode the done quantities.'))

        if picking_type.use_create_lots or picking_type.use_existing_lots:
            lines_to_check = self.move_line_ids
            if not no_quantities_done:
                lines_to_check = lines_to_check.filtered(
                    lambda line: float_compare(line.qty_done, 0,
                                               precision_rounding=line.product_uom_id.rounding)
                )

            for line in lines_to_check:
                product = line.product_id
                if product and product.tracking != 'none':
                    if not line.lot_name and not line.lot_id:
                        raise UserError(_('You need to supply a Lot/Serial number for product %s.') % product.display_name)

        # Propose to use the sms mechanism the first time a delivery
        # picking is validated. Whatever the user's decision (use it or not),
        # the method button_validate is called again (except if it's cancel),
        # so the checks are made twice in that case, but the flow is not broken
        sms_confirmation = self._check_sms_confirmation_popup()
        if sms_confirmation:
            return sms_confirmation

        if no_quantities_done:
            view = self.env.ref('stock.view_immediate_transfer')
            wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
            return {
                'name': _('Immediate Transfer?'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'stock.immediate.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
            view = self.env.ref('stock.view_overprocessed_transfer')
            wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': self.id})
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'stock.overprocessed.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        # Check backorder should check for other barcodes
        if self._check_backorder():
            return self.action_generate_backorder_wizard()
        self.action_done()
        return



    @api.onchange('is_nonsalealewarehouse_transfar')
    def select_nonsale_ale_stock(self):

        """
        this method is used for transfar page when select lim transfar then it show only lim transfar
        :return:
        """
        self.branch_id = self.env.user.branch_id
        if self.is_nonsalealewarehouse_transfar:
            self.is_nonsalealewarehouse_transfar = True
            print('come to condition is_nonsalealewarehouse_transfar')
            warehouse = self.env['stock.warehouse'].sudo().search([('is_non_saleable_warehouse', '=', True),('company_id', '=',self.env.user.company_id.id)], limit=1)
            print(warehouse.id)
            picking_type = self.env['stock.picking.type'].sudo().search(
                [('warehouse_id', '=', warehouse.id), ('sequence_code', '=', 'INT')])
            print(picking_type)
            print(picking_type.warehouse_id.name)
            self.picking_type_id = picking_type.id

            return {
                'domain': {
                    'picking_type_id': [('warehouse_id', '=', warehouse.id), ('sequence_code', '=', 'INT')]
                },
                # 'default_picking_type_id': [('warehouse_id', '=', warehouse.id), ('sequence_code', '=', 'INT')]
                # lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_src_id

            }
        else:
            return {
                'domain': {
                    'picking_type_id': []
                }
            }

    # def _do_partial_func_unreserved(self):
    #     print('_do_partial_unreserved')

    # @api.onchange('fpo_order_id')
    # def fpo_fall_into(self):
    #     print('work')

    is_nonsalealewarehouse_transfar = fields.Boolean(string='Lim transfar ', default=False)
    commercial_invoice = fields.Many2one('account.move',domain=[('type','=','in_invoice')],string="Commercial Invoice")

    def action_assign(self):
        """ Check availability of picking moves.
        This has the effect of changing the state and reserve quants on available moves, and may
        also impact the state of the picking as it is computed based on move's states.
        @return: True
        """
        res = {}
        self.filtered(lambda picking: picking.state == 'draft').action_confirm()
        moves = self.mapped('move_lines').filtered(lambda move: move.state not in ('draft', 'cancel', 'done'))
        if not moves:
            raise UserError(_('Nothing to check the availability for.'))
        # If a package level is done when confirmed its location can be different than where it will be reserved.
        # So we remove the move lines created when confirmed to set quantity done to the new reserved ones.
        package_level_done = self.mapped('package_level_ids').filtered(
            lambda pl: pl.is_done and pl.state == 'confirmed')
        package_level_done.write({'is_done': False})
        is_raise_validation_error = moves._action_assign()

        package_level_done.write({'is_done': True})
        if is_raise_validation_error:
            # message = 'product is no available '
            # raise osv.except_osv(_('warning'), _(message))
            # res['warning'] = {'title': _('Warning'), 'message': message}
            # raise ValueError('product not available')
            raise ValidationError('product is no available ')

        return True

    # fpo_order_id = fields.Many2one('foreign.purchase.order', string= 'Foreign purchase order ')

    # @api.onchange('move_ids_without_package.product_uom_qty')
    #     # def test(self):
    #     #     print('***********************')
    #     #     print('***********************')
    #     #     print('***********************')
