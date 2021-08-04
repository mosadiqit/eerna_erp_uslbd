from datetime import date, datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from collections import defaultdict

from odoo.osv.osv import osv

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'out_receipt': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
    'in_receipt': 'supplier',
}


class AccountBatchPaymentInherit(models.Model):
    _inherit = 'account.payment'

    batch_payment_id = fields.Many2one('batch.payment', string='Batch Payment Reference')
    bank_id = fields.Many2one('bank_info.all_bank', string="Bank")
    in_treatment_state = fields.Boolean(string="In Treatment State")
    treatment_id = fields.Many2one('batch.payment.test', string="Cheque Treatment")
    collection_reference = fields.Selection([
        ('advance_collection', 'Advance Collection'),
        ('previous_invoice', 'Previous Invoice'),
        ('multiple_invoice', 'Multiple Invoice'),
        ('cheque_adjustment', 'Cheque Adjustment')], string="Collection Reference")

    invoice_start_date = fields.Date(string="Invoice Start Date", default=fields.Date.context_today, store=False)
    invoice_end_date = fields.Date(string="Invoice End Date", default=fields.Date.context_today, store=False)
    payment_invoice_ids = fields.Many2many('account.move', 'invoice_wise_account_payment_rel', 'payment_id', 'invoice_id', string="Multiple Invoice Reference",
                                           domain="[('partner_id', '=', partner_id), ('state', '=', 'posted'), ('invoice_payment_state', '=', 'not_paid'), "
                                                  "('date', '<=', invoice_end_date), ('date', '>=', invoice_start_date), ('type', '=', 'out_invoice')]")
    draft_account_move_id = fields.Many2one('account.move', string="Draft Account Move ID")
    bank_issue_account_move_id = fields.Many2one('account.move', string="Bank Issue Account Move")
    dishonor_balance_adjust_amt = fields.Monetary(string="Dishonor Balance Adjustment")
    dishonor_collection_ids = fields.Many2many('account.payment', 'account_payment_dishonor_collection_rel', 'dishonor_id', 'collection_id', string='Dishonor Collections', domain="[('state', '=', 'dishonored'), ('dishonor_balance_adjust_amt', '!=', amount), ('partner_id', '=', partner_id)]")
    total_due = fields.Float(string="Total Due", store=False)
    not_respone_by_effective_date = fields.Boolean(string="Not response in duration of effective date")


    state = fields.Selection([
        ('init', 'Initial'),
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('dishonored', 'Dishonored'),
        ('waiting_for_approval', 'Waiting For Approval'),
        ('posted', 'Validated'),
        ('reconciled', 'Reconciled'),
        ('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status", tracking=4)

    @api.model
    def dishonor_scheduling(self):
        dishonor_payment_list = self.env['account.payment'].search([('state', '=', 'waiting_for_approval'), ('effective_date', '=', (date.today() - timedelta(3)))])
        for dishonor_payment in dishonor_payment_list:
            self.env['cheque.treatment'].dishonor_payment(dishonor_payment)
            dishonor_payment.not_respone_by_effective_date = True

    def name_get(self):
        result = []
        for payment_line in self:
            name = ""
            if payment_line.cheque_reference:
                name = payment_line.cheque_reference + ' - '
            if payment_line.name:
                name += payment_line.name
            if payment_line.amount:
                name += 'Amount = (' + str(payment_line.amount) + ' '
                if payment_line.currency_id:
                    name += str(payment_line.currency_id.name)
                name += ' )'
            result.append((payment_line.id, name))
        return result

    @api.onchange('cheque_reference')
    def _onchange_cheque_reference(self):
        exists = False
        for record in self:
            if record.cheque_reference:
                domain = [('cheque_reference', '=', record.cheque_reference)]
                exists = super(AccountBatchPaymentInherit, self).search(domain, limit=100).name_get()
            if exists:
                raise UserError('Cheque No "' + record.cheque_reference + '" is already in stored!')

    @api.onchange('collection_reference')
    def _onchange_collection_reference(self):
        if self.collection_reference == 'cheque_adjustment':
            return {'domain':{'payment_method_id':[('code','=','manual'), ('payment_type','=','outbound')]}}
        else:
            if self.journal_id:
                if self.journal_id.currency_id:
                    self.currency_id = self.journal_id.currency_id

                # Set default payment method (we consider the first to be the default one)
                payment_methods = self.payment_type == 'inbound' and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
                payment_methods_list = payment_methods.ids

                default_payment_method_id = self.env.context.get('default_payment_method_id')
                if default_payment_method_id:
                    # Ensure the domain will accept the provided default value
                    payment_methods_list.append(default_payment_method_id)
                else:
                    self.payment_method_id = payment_methods and payment_methods[0] or False

                # Set payment method domain (restrict to methods enabled for the journal and to selected payment type)
                payment_type = self.payment_type in ('outbound', 'transfer') and 'outbound' or 'inbound'

                user_id = self.env.user.id
                user = self.env['res.users'].search([('id', '=', user_id)], limit=1)
                res_groups = self.env['res.groups'].search([('name', '=', 'TT Collector')], limit=1)
                tt_collector = False
                if user:
                    for grp_id in user.groups_id:
                        if grp_id.id == res_groups.id:
                            tt_collector = True

                if tt_collector:
                    domain = {
                        'payment_method_id': [('payment_type', '=', payment_type), ('id', 'in', payment_methods_list)]}
                else:
                    domain = {
                        'payment_method_id': [('payment_type', '=', payment_type), ('code', '!=', 'tt'), ('id', 'in', payment_methods_list)]}

                if self.env.context.get('active_model') == 'account.move':
                    active_ids = self._context.get('active_ids')
                    invoices = self.env['account.move'].browse(active_ids)
                    self.amount = abs(
                        self._compute_payment_amount(invoices, self.currency_id, self.journal_id, self.payment_date))

                return {'domain': domain}
            return {}


class AccountBatchPayment(models.Model):
    _name = "batch.payment"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Batch Payments"

    batch_payment_line = fields.One2many('account.payment', 'batch_payment_id', string='Batch Payment Lines')
    payment_type = fields.Selection(
        [('outbound', 'Send Money'), ('inbound', 'Receive Money'), ('transfer', 'Internal Transfer')],
        string='Payment Type', required=True, readonly=True, states={'initial': [('readonly', False)]})
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')], tracking=True, readonly=True, states={'initial': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', string='Partner', tracking=True, readonly=True, states={'initial': [('readonly', False)]}, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    payment_date = fields.Date(string='Date', default=fields.Date.context_today, required=True, readonly=True,
                               states={'initial': [('readonly', False)]}, copy=False, tracking=True)
    branch_id = fields.Many2one('res.branch', string="Branch", required=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        index=True,
        default=lambda self: self.env.company.id)

    dishonor_cheque_list = fields.Many2many('account.payment', 'account_payment_dishonor_rel', 'line_id', 'dishonor_id', store=False, string="Dishonor Cheques")

    draft_journal_id = fields.Integer("Draft Journal ID", default=lambda self: self.load_draft_journal_id())
    state = fields.Selection(
        [('initial', 'Initial'), ('processing', 'Processing'), ('dishonor', 'Dishonor'), ('approve', 'Approve'), ('finished', 'Finished')], readonly=True, default='initial', copy=False, string="Status")

    @api.model
    def load_draft_journal_id(self):
        query = """
                select id from account_journal where default_credit_account_id = 
                    (select cheque_in_hand_account_id from saleotherexpense where company_id = {} limit 1) limit 1
                    """.format(self.env.user.company_id.id)
        self._cr.execute(query=query)
        query_result = self._cr.fetchall()
        if query_result:
            return query_result[0][0]

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        for item in self:
            pay_type = item.payment_type
            print(item.batch_payment_line)
            for line in item.batch_payment_line:
                line.payment_type = pay_type

    @api.onchange('batch_payment_line')
    def onchange_batch_payment_line(self):
        list = [(5, 0, 0)]
        for payment_line in self.batch_payment_line:
            if payment_line.dishonor_collection_ids:
                for item in payment_line.dishonor_collection_ids:
                    list.append((0, 0, {
                            'id': item.id,
                            'payment_type': item.payment_type,
                            'payment_date': item.payment_date,
                            'name': item.name,
                            'payment_method_id': item.payment_method_id,
                            'partner_id': item.partner_id,
                            'amount': item.amount,
                            'state': item.state,
                            'company_id': item.company_id,
                            'cheque_reference': item.cheque_reference,
                            'dishonor_balance_adjust_amt': item.dishonor_balance_adjust_amt,
                            'total_due': item.amount-item.dishonor_balance_adjust_amt,
                        }))
                self.dishonor_cheque_list = list

    # @api.model
    # def create(self, vals_List):
    #     self.state = 'processing'
    #     vals_List.state = 'processing'
    #     res = super(AccountBatchPayment, self).create(vals_List)
    #     return res
    #
    # @api.model_create_multi
    # def create(self, vals_List):
    #     self.state = 'processing'
    #     for items in vals_List:
    #
    #         new_value = dict({'state': 'processing'})
    #         items.update(new_value)
    #
    #         if 'batch_payment_line' in items.keys():
    #             for line_details in items['batch_payment_line']:
    #                 for line in line_details:
    #                     print(line)
    #                     if isinstance(line, dict):
    #                         if 'payment_type' in line.keys():
    #                             payment_type_dc = {'payment_type': 'inbound'}
    #                             state_dc = {'state': 'init'}
    #                             partner_type_dc = {'partner_type': vals_List[0]['partner_type']}
    #                             partner_id_dc = {'partner_id': vals_List[0]['partner_id']}
    #                             branch_id_dc = {'branch_id': vals_List[0]['branch_id']}
    #                             line.update(payment_type_dc)
    #                             line.update(state_dc)
    #                             line.update(partner_type_dc)
    #                             line.update(partner_id_dc)
    #                             line.update(branch_id_dc)
    #
    #     res = super(AccountBatchPayment, self).create(vals_List)

    def btn_dishonor_all(self):
        for record in self:
            record.state = 'dishonor'

    def btn_submit_for_approval(self):
        print("Submit For Approval")
        self.state = 'processing'
        for line_details in self.batch_payment_line:
            payment_type_dc = {'payment_type': 'inbound'}
            state_dc = {'state': 'init'}
            partner_type_dc = {'partner_type': self.partner_type}
            partner_id_dc = {'partner_id': self.partner_id}
            branch_id_dc = {'branch_id': self.branch_id}
            line_details.update(payment_type_dc)
            line_details.update(state_dc)
            line_details.update(partner_type_dc)
            line_details.update(partner_id_dc)
            line_details.update(branch_id_dc)
            # for line in line_details:
            #     if isinstance(line, dict):
            #         if 'payment_type' in line.keys():
            #             payment_type_dc = {'payment_type': 'inbound'}
            #             state_dc = {'state': 'init'}
            #             partner_type_dc = {'partner_type': self.partner_type}
            #             partner_id_dc = {'partner_id': self.partner_id}
            #             branch_id_dc = {'branch_id': self.branch_id}
            #             line.update(payment_type_dc)
            #             line.update(state_dc)
            #             line.update(partner_type_dc)
            #             line.update(partner_id_dc)
            #             line.update(branch_id_dc)

            # new_value = dict({'state': 'processing'})
            # items.update(new_value)
            #
            # if 'batch_payment_line' in items.keys():
            #     for line_details in items['batch_payment_line']:
            #         for line in line_details:
            #             if isinstance(line, dict):
            #                 if 'payment_type' in line.keys():
            #                     payment_type_dc = {'payment_type': 'inbound'}
            #                     state_dc = {'state': 'init'}
            #                     partner_type_dc = {'partner_type': self.partner_type}
            #                     partner_id_dc = {'partner_id': self.partner_id}
            #                     branch_id_dc = {'branch_id': self.branch_id}
            #                     line.update(payment_type_dc)
            #                     line.update(state_dc)
            #                     line.update(partner_type_dc)
            #                     line.update(partner_id_dc)
            #                     line.update(branch_id_dc)

    def btn_approve(self):
        for record in self:
            record.state = 'approve'

        for payment_line in self.batch_payment_line:

            # if payment_line.state == 'waiting_for_approval':
            AccountMove = self.env['account.move'].with_context(default_type='entry')
            for rec in payment_line:
                # payment_line.honor_date = date.today()
                payment_line.honor_date = self.payment_date

                if any(inv.state != 'posted' for inv in rec.invoice_ids):
                    raise ValidationError(
                        _("The payment cannot be processed because the invoice is not open!"))

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
                    rec.name = self.env['ir.sequence'].next_by_code(sequence_code,
                                                                    sequence_date=rec.payment_date)
                    if not rec.name and rec.payment_type != 'transfer':
                        raise UserError(
                            _("You have to define a sequence for %s in your company.") % (sequence_code,))

                    given_invoice_ids = self.get_given_invoices(rec)

                    rec.update({
                        'invoice_ids': [(6, 0, given_invoice_ids)],
                    })

                    # moves.date = rec.effective_date
                    moves = AccountMove.create(rec._prepare_payment_moves())
                    for line in moves.invoice_line_ids:
                        line.collection_date=self.payment_date
                    # moves.collection_date=self.payment_date
                    if rec.effective_date:
                        moves.date = rec.effective_date
                    else:
                        moves.date = datetime.now()

                    if (rec.payment_method_id.code in ['tt', 'manual']):
                        moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()

                        # Update the state / move before performing any reconciliation.
                        move_name = payment_line._get_move_name_transfer_separator().join(moves.mapped('name'))
                        rec.write({'state': 'posted', 'move_name': move_name})

                        if rec.payment_type in ('inbound', 'outbound'):
                            # ==== 'inbound' / 'outbound' ====
                            if rec.invoice_ids:
                                (moves[0] + rec.invoice_ids).line_ids \
                                    .filtered(
                                    lambda line: not line.reconciled and line.account_id == rec.destination_account_id) \
                                    .reconcile()
                        elif rec.payment_type == 'transfer':
                            # ==== 'transfer' ====
                            moves.mapped('line_ids') \
                                .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id) \
                                .reconcile()
                    # moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()
                    else:
                        # Update the state / move before performing any reconciliation.
                        move_name = payment_line._get_move_name_transfer_separator().join(moves.mapped('name'))
                        rec.write({'state': 'draft', 'move_name': move_name, 'draft_account_move_id': moves.id})
                        #
                        # if rec.payment_type in ('inbound', 'outbound'):
                        #     # ==== 'inbound' / 'outbound' ====
                        #     if rec.invoice_ids:
                        #         (moves[0] + rec.invoice_ids).line_ids \
                        #             .filtered(
                        #             lambda
                        #                 line: not line.reconciled and line.account_id == rec.destination_account_id) \
                        #             .reconcile()
                        # elif rec.payment_type == 'transfer':
                        #     # ==== 'transfer' ====
                        #     moves.mapped('line_ids') \
                        #         .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id) \
                        #         .reconcile()




        for payment_line in self.batch_payment_line:
            if payment_line.state == 'cancelled':
                payment_line.state = 'draft'

    def get_given_invoices(self, batch_payment):
        given_invoice_ids = []
        if batch_payment.collection_reference == 'multiple_invoice':
            for given_invoice in batch_payment.payment_invoice_ids:
                given_invoice_ids.append(given_invoice.id)

        elif batch_payment.collection_reference == 'previous_invoice':
            query = """                        
                        select am.id from account_move am 
                        left join invoice_wise_account_payment_rel amr on am.id = amr.invoice_id
                        where type = 'out_invoice' and partner_id = {}
                        and state = 'posted' 
                        and invoice_payment_state = 'not_paid'
                        and amr.invoice_id is null order by id asc""".format(batch_payment.partner_id.id)

            self._cr.execute(query=query)
            query_result = self._cr.fetchall()

            if query_result:
                for given_invoice in query_result:
                    if given_invoice:
                        given_invoice_ids.append(given_invoice[0])

        elif batch_payment.collection_reference == 'cheque_adjustment':
            for dishonor_cheque in batch_payment.dishonor_collection_ids:
                for invoices in dishonor_cheque.payment_invoice_ids:
                    given_invoice_ids.append(invoices.id)

        return given_invoice_ids


class AccountMoveLineInherit(models.Model):
    _inherit="account.move.line"

    collection_date = fields.Date(string="collection Date")