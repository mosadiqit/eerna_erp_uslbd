from collections import Counter

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.exceptions import UserError, ValidationError


class customStockPicking(models.Model):
    # _name = 'stock.picking'
    _inherit = 'stock.picking'

    # check_validate=fields.Boolean(compute='_check_validate',default=False)
    check_approval = fields.Boolean(compute='_check_approval', default=False)
    partner_id = fields.Many2one(
        'res.partner', 'Contact',
        check_company=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, domain=lambda self: self.filteredID())
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('approval', 'Approval'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, tracking=True,
        help=" * Draft: The transfer is not confirmed yet. Reservation doesn't apply.\n"
             " * Waiting another operation: This transfer is waiting for another operation before being ready.\n"
             " * Waiting: The transfer is waiting for the availability of some products.\n(a) The shipping policy is \"As soon as possible\": no product could be reserved.\n(b) The shipping policy is \"When all products are ready\": not all the products could be reserved.\n"
             " * Ready: The transfer is ready to be processed.\n(a) The shipping policy is \"As soon as possible\": at least one product has been reserved.\n(b) The shipping policy is \"When all products are ready\": all product have been reserved.\n"
             " * Done: The transfer has been processed.\n"
             " * Cancelled: The transfer has been cancelled.")

    state_a = fields.Selection(related='state')
    state_b = fields.Selection(related='state')

    def filteredID(self):
        print(self._uid)
        query = """select partner_id from res_users where show_users=true and id !={}""".format(self._uid)
        self._cr.execute(query=query)
        query_res = self._cr.fetchall()
        partner_ids = []
        for id in query_res:
            partner_ids.append(id[0])
        print(partner_ids)
        return [('id', 'in', partner_ids)]

    def button_submit_approval(self):
        for rec in self.move_lines:
            if rec.product_uom_qty != rec.reserved_availability and 'INT' in (self.name).split(
                    "/"):
                print('demand and reserved not match please check .')
                raise ValidationError("demand and reserved not match please check .")

        for rec in self:
            rec.state = 'approval'

    @api.depends('move_type', 'immediate_transfer', 'move_lines.state', 'move_lines.picking_id')
    def _compute_state(self):
        print(self)
        ''' State of a picking depends on the state of its related stock.move
        - Draft: only used for "planned pickings"
        - Waiting: if the picking is not ready to be sent so if
          - (a) no quantity could be reserved at all or if
          - (b) some quantities could be reserved and the shipping policy is "deliver all at once"
        - Waiting another move: if the picking is waiting for another move
        - Ready: if the picking is ready to be sent so if:
          - (a) all quantities are reserved or if
          - (b) some quantities could be reserved and the shipping policy is "as soon as possible"
        - Done: if the picking is done.
        - Cancelled: if the picking is cancelled
        '''
        for picking in self:
            if not picking.move_lines:
                picking.state = 'draft'
            elif any(move.state == 'draft' for move in picking.move_lines):  # TDE FIXME: should be all ?
                picking.state = 'draft'
            elif all(move.state == 'cancel' for move in picking.move_lines):
                picking.state = 'cancel'
            elif all(move.state in ['cancel', 'done'] for move in picking.move_lines):
                picking.state = 'done'
            else:
                relevant_move_state = picking.move_lines._get_relevant_state_among_moves()
                if picking.immediate_transfer and relevant_move_state not in ('draft', 'cancel', 'done'):
                    picking.state = 'assigned'
                elif relevant_move_state == 'partially_available':
                    picking.state = 'assigned'
                else:
                    picking.state = relevant_move_state

    @api.depends('state')
    def _check_approval(self):
        query = """select partner_id from res_users where id={}""".format(self._uid)
        self._cr.execute(query=query)
        loged_user_id = self._cr.fetchone()
        print(loged_user_id[0])
        print(self.partner_id.id)
        # if self.state !=False:
        if self.state in 'approval,confirmed,assigned':
            if loged_user_id[0] == self.partner_id.id:
                self.check_approval = True
            else:
                self.check_approval = False
        print(self.check_approval)

    # def action_assign(self):
    #     """ Check availability of picking moves.
    #     This has the effect of changing the state and reserve quants on available moves, and may
    #     also impact the state of the picking as it is computed based on move's states.
    #     @return: True
    #     """
    #     self.filtered(lambda picking: picking.state == 'draft').action_confirm()
    #     moves = self.mapped('move_lines').filtered(lambda move: move.state not in ('draft', 'cancel', 'done','approval','assigned'))
    #     if not moves:
    #         raise UserError(_('Nothing to check the availability for.'))
    #     # If a package level is done when confirmed its location can be different than where it will be reserved.
    #     # So we remove the move lines created when confirmed to set quantity done to the new reserved ones.
    #     package_level_done = self.mapped('package_level_ids').filtered(
    #         lambda pl: pl.is_done and pl.state == 'confirmed')
    #     package_level_done.write({'is_done': False})
    #     moves._action_assign()
    #     package_level_done.write({'is_done': True})
    #     return True

    # class customStockPicking(models.Model):
    #     # _name = 'stock.picking'
    #     _inherit = 'stock.move.line'
    #
    #     @api.onchange('lot_name', 'lot_id')
    #     def onchange_serial_number(self):
    #         """ When the user is encoding a move line for a tracked product, we apply some logic to
    #         help him. This includes:
    #             - automatically switch `qty_done` to 1.0
    #             - warn if he has already encoded `lot_name` in another move line
    #         """
    #         res = {}
    #         if self.product_id.tracking == 'serial':
    #             if not self.qty_done:
    #                 self.product_uom_qty = 1
    #
    #             message = None
    #             if self.lot_name or self.lot_id:
    #                 move_lines_to_check = self._get_similar_move_lines() - self
    #                 if self.lot_name:
    #                     counter = Counter([line.lot_name for line in move_lines_to_check])
    #                     if counter.get(self.lot_name) and counter[self.lot_name] > 1:
    #                         message = _(
    #                             'You cannot use the same serial number twice. Please correct the serial numbers encoded.')
    #                 elif self.lot_id:
    #                     counter = Counter([line.lot_id.id for line in move_lines_to_check])
    #                     if counter.get(self.lot_id.id) and counter[self.lot_id.id] > 1:
    #                         message = _(
    #                             'You cannot use the same serial number twice. Please correct the serial numbers encoded.')
    #
    #             if message:
    #                 res['warning'] = {'title': _('Warning'), 'message': message}
    #         return res
