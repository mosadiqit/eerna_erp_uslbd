# -*- coding: utf-8 -*-
from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from collections import defaultdict

class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'
    _description = 'customer payment state update'

    set_flag=fields.Boolean('Flag' ,compute='_set_flag' ,default=False)

    # @api.depends('state')
    def _set_flag(self):
        print(self)
        query="""select ru.branch_id from account_payment ap
                    left join res_users ru on ru.id=ap.create_uid where ap.id={}""".format(self.id)
        self._cr.execute(query=query)
        created_user_branch_id=self._cr.fetchone()
        query="""select branch_id from res_users where id={}""".format(self._uid)
        self._cr.execute(query=query)
        logged_user_in_branch = self._cr.fetchone()
        if created_user_branch_id==logged_user_in_branch:
            self.set_flag=True
        else:
            self.set_flag=False

        # logged_user=self._uid
        # access_group_user


    def submit_for_approval(self):
        for rec in self:

            # print('User', self.env.user)
            logged_user=self._uid
            print(logged_user)
            get_logged_user_branch=self.env['res.users'].search([('id','=',self._uid)]).branch_id
            print(get_logged_user_branch.id)
            _default_warehouse = self.env.user.context_default_warehouse_id.name
            approved_setting = self.env['customer.payment.approval'].search([])
            if approved_setting.approve_customer_payment:
                rec.state = 'waiting_for_approval'
                partner_ids = []
                display_message = 'An customer payment is posted on the "waiting for approval" state. Please approve it.'
                for approver in approved_setting.customer_payment_approver_ids:
                    get_approval_user_branch = self.env['res.users'].search([('id', '=', approver.id)]).branch_id
                    print(get_approval_user_branch.id)
                    # print('Salesman Default warehouse', salesman_default_warehouse)
                    # print('Approver Default warehouse', approver.context_default_warehouse_id.name)
                    if get_logged_user_branch.id == get_approval_user_branch.id:
                    # if approver.context_default_warehouse_id.name == _default_warehouse:
                        approver.notify_info(message=display_message)
                        partner_ids.append(self.env['res.partner'].search([('name', 'ilike', approver.name)], limit=1).id)

                # sale_order = self.env['sale.order'].browse(self.env.context.get('active_ids'))
                rec.message_post(body=display_message, subtype='mt_note', partner_ids=partner_ids)
            else:
                rec.state = 'sent'

    def approve_custom_payment(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the src liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconcilable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        AccountMove = self.env['account.move'].with_context(default_type='entry')
        for rec in self:
            self.honor_date=date.today()
            if rec.state != 'waiting_for_approval':
                raise UserError(_("Only a waiting for approval payment can be posted."))

            if any(inv.state != 'posted' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # keep the name in case of a payment reset to draft
            if not rec.name:
                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                rec.name = self.env['ir.sequence'].next_by_code(sequence_code, sequence_date=rec.payment_date)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            moves = AccountMove.create(rec._prepare_payment_moves())
            moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()

            # Update the state / move before performing any reconciliation.
            move_name = self._get_move_name_transfer_separator().join(moves.mapped('name'))
            rec.write({'state': 'posted', 'move_name': move_name})

            if rec.payment_type in ('inbound', 'outbound'):
                # ==== 'inbound' / 'outbound' ====
                if rec.invoice_ids:
                    (moves[0] + rec.invoice_ids).line_ids \
                        .filtered(lambda line: not line.reconciled and line.account_id == rec.destination_account_id) \
                        .reconcile()
            elif rec.payment_type == 'transfer':
                # ==== 'transfer' ====
                moves.mapped('line_ids') \
                    .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id) \
                    .reconcile()

        return True




    state = fields.Selection([
        ('draft', 'Draft'),
        ('dishonored', 'Dishonored'),
        ('waiting_for_approval', 'Waiting For Approval'),
        ('posted', 'Validated'),
        ('sent', 'Sent'),

        ('reconciled', 'Reconciled'),
        ('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status",tracking=4)


    # state = fields.Selection([
    #     ('draft', 'Quotation'),
    #     ('sent', 'Quotation Sent'),
    #     ('waiting_for_approval', 'Waiting For Approval'),
    #     ('sale', 'Sales Order'),
    #     ('done', 'Locked'),
    #     ('cancel', 'Cancelled'),
    # ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')


# class SaleOrderCancelReason(models.Model):
#     _name = "customer.payment.cancel.reason"
#     _description = 'Customer Payment Cancel Reason'
#
#     name = fields.Char('Description', required=True, translate=True)
#     active = fields.Boolean('Active', default=True)
