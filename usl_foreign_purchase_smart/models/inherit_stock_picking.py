from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES


class InheritStockPicking_Foreign(models.Model):
    _inherit = "stock.picking"

    def button_validate_foreign(self,name=None):


        # Clean-up the context key at validation to avoid forcing the creation of immediate
        # transfers.
        print(name)

        picking_ids=self.env['stock.picking'].search([('origin','=',name)])
        picking_ids.button_validate_ci()

    def button_validate_ci(self):
        self.ensure_one()
        if not self.move_lines and not self.move_line_ids:
            raise UserError(_('Please add some items to move.'))

        # Clean-up the context key at validation to avoid forcing the creation of immediate
        # transfers.
        ctx = dict(self.env.context)
        ctx.pop('default_immediate_transfer', None)
        self = self.with_context(ctx)

        # add user as a follower
        self.message_subscribe([self.env.user.partner_id.id])

        # If no lots when needed, raise error
        picking_type = self.picking_type_id
        # precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        # no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in self.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
        no_quantities_done=False
        no_reserved_quantities = all(float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in self.move_line_ids)
        if no_reserved_quantities and no_quantities_done:
            raise UserError(_('You cannot validate a transfer if no quantites are reserved nor done. To force the transfer, switch in edit more and encode the done quantities.'))

        # if picking_type.use_create_lots or picking_type.use_existing_lots:
        #     lines_to_check = self.move_line_ids
        #     if not no_quantities_done:
        #         lines_to_check = lines_to_check.filtered(
        #             lambda line: float_compare(line.qty_done, 0,
        #                                        precision_rounding=line.product_uom_id.rounding)
        #         )
        #
        #     for line in lines_to_check:
        #         product = line.product_id
        #         if product and product.tracking != 'none':
        #             if not line.lot_name and not line.lot_id:
        #                 raise UserError(_('You need to supply a Lot/Serial number for product %s.') % product.display_name)

        # Propose to use the sms mechanism the first time a delivery
        # picking is validated. Whatever the user's decision (use it or not),
        # the method button_validate is called again (except if it's cancel),
        # so the checks are made twice in that case, but the flow is not broken
        sms_confirmation = self._check_sms_confirmation_popup()
        if sms_confirmation:
            return sms_confirmation

        # if no_quantities_done:
        #     view = self.env.ref('stock.view_immediate_transfer')
        #     wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
        #     return {
        #         'name': _('Immediate Transfer?'),
        #         'type': 'ir.actions.act_window',
        #         'view_mode': 'form',
        #         'res_model': 'stock.immediate.transfer',
        #         'views': [(view.id, 'form')],
        #         'view_id': view.id,
        #         'target': 'new',
        #         'res_id': wiz.id,
        #         'context': self.env.context,
        #     }
        #
        # if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
        #     view = self.env.ref('stock.view_overprocessed_transfer')
        #     wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': self.id})
        #     return {
        #         'type': 'ir.actions.act_window',
        #         'view_mode': 'form',
        #         'res_model': 'stock.overprocessed.transfer',
        #         'views': [(view.id, 'form')],
        #         'view_id': view.id,
        #         'target': 'new',
        #         'res_id': wiz.id,
        #         'context': self.env.context,
        #     }

        # Check backorder should check for other barcodes
        # if self._check_backorder():
        #     return self.action_generate_backorder_wizard()
        move_id = self.env['stock.move'].search([('id','in',self.move_lines.ids)])
        active_model = self.env.context.get('active_model')
        print(active_model)
        # if active_model == 'foreign.purchase.order':
        move_id._action_done()
        return
