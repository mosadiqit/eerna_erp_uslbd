from datetime import date, datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountVendorBatchPayment(models.Model):
    _name = "vendor.batch.payment"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Vendor Batch Payments"

    name = fields.Char(string="Transaction No", readOnly=True)
    batch_payment_line = fields.One2many('account.payment', 'batch_payment_id', string='Batch Payment Lines')
    payment_type = fields.Selection(
        [('outbound', 'Send Money'), ('inbound', 'Receive Money'), ('transfer', 'Internal Transfer')],
        string='Payment Type', required=True, readonly=True, states={'initial': [('readonly', False)]})
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')], tracking=True, readonly=True,
                                    states={'initial': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', string='Partner', tracking=True, readonly=True,
                                 states={'initial': [('readonly', False)]},
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    payment_date = fields.Date(string='Date', default=fields.Date.today, required=True, readonly=True,
                               states={'initial': [('readonly', False)]}, copy=False, tracking=True)
    branch_id = fields.Many2one('res.branch', string="Branch", required=True,
                                domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        index=True,
        default=lambda self: self.env.company.id)

    dishonor_cheque_list = fields.Many2many('account.payment', 'account_payment_dishonor_rel', 'line_id', 'dishonor_id',
                                            store=False, string="Dishonor Cheques")

    draft_journal_id = fields.Integer("Draft Journal ID", default=lambda self: self.load_draft_journal_id())
    state = fields.Selection(
        [('initial', 'Initial'), ('processing', 'Processing'), ('dishonor', 'Dishonor'), ('approve', 'Approve'),
         ('finished', 'Finished')], readonly=True, default='initial', copy=False, string="Status")
    entry_by = fields.Many2one('res.users', string="Entry By")
    collected_by = fields.Many2one('res.users', string="Collected By", default=lambda self: self.env.user.id)
    approved_by = fields.Many2one('res.users', string="Approve By")
    approved_date = fields.Date(string='Approve Date')

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

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.branch_id = self.env['res.branch'].search([('company_id', '=', self.company_id.id)])

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for line in self.batch_payment_line:
            line.partner_id = self.partner_id

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
                        'total_due': item.amount - item.dishonor_balance_adjust_amt,
                    }))
                self.dishonor_cheque_list = list

    @api.model
    def create(self, vals):
        upd_vals = vals.copy()
        if upd_vals.get("name", "/") == "/":
            upd_vals["name"] = self.env["ir.sequence"].next_by_code("batch.payment.no")
        if 'batch_payment_line' in vals.keys():
            if vals['batch_payment_line']:
                for line in vals['batch_payment_line']:
                    line[2]['initial_create_status'] = True

        return super().create(upd_vals)

    def btn_dishonor_all(self):
        for record in self:
            record.state = 'dishonor'

    def check_validation(self, payment_info):
        status = False
        message = ""
        if not payment_info.collection_reference:
            message += "Collection Reference should not be empty\n"
            status = True

        if payment_info.collection_reference == 'cheque_adjustment':
            if payment_info.payment_method_id.code != 'manual':
                message += "Payment Method should be Cash Type for Cheque Adjustment Collection\n"
                status = True

        if payment_info.collection_reference == 'cheque_adjustment':
            if payment_info.payment_method_id.code != 'manual':
                message += "Payment Method should be Cash Type for Cheque Adjustment Collection\n"
                status = True

        if payment_info.collection_reference == 'multiple_invoice':
            if not payment_info.payment_invoice_ids:
                message += "Invoice can not be empty in Collection Reference of Multiple Invoice\n"
                status = True

        if payment_info.amount < 1:
            message += "Amount should be greater than 0\n"
            status = True

        if payment_info.payment_method_id.code in ['check_in', 'pdc']:
            if not payment_info.effective_date:
                message += "Effective Date should not be empty\n"
                status = True

        if payment_info.payment_method_id.code in ['check_in', 'pdc', 'tt']:
            if not payment_info.bank_id:
                message += "Bank should not be empty\n"
                status = True

            if not payment_info.cheque_reference:
                message += "Cheque Reference should not be empty\n"
                status = True

        if payment_info.collection_reference == 'cheque_adjustment':
            if len(payment_info.dishonor_collection_ids) > 0:
                dishonor_amt = 0
                for dishonor_cheq in payment_info.dishonor_collection_ids:
                    dishonor_amt += (dishonor_cheq.amount - dishonor_cheq.dishonor_balance_adjust_amt)

                if dishonor_amt < payment_info.amount:
                    message += "Collection amount cannot be greater than total dishonor cheque's amount\n"
                    status = True
            else:
                message += "Dishonor Collection list should be empty\n"
                status = True

        if status:
            return message
        return status

    def _get_journal_id_by_query(self, query):
        self._cr.execute(query=query)
        query_result = self._cr.fetchall()
        if query_result:
            journal_id = query_result[0][0]
        else:
            raise UserError(
                _("Journal not found\nPlease, select journal/ configure journal by Company"))
        return journal_id

    def set_journal_id(self, line_details):

        if line_details.payment_method_id.code == 'manual':
            query = """
                                        select id from account_journal where type = 'cash' and company_id = {} limit 1
                                            """.format(self.env.user.company_id.id)
            line_details.journal_id = self._get_journal_id_by_query(query)
        elif line_details.payment_method_id.code == 'tt':
            if line_details.tt_sent_journal_id:
                line_details.journal_id = line_details.tt_sent_journal_id
            else:
                raise ValidationError(_("TT sent journal cannot be empty for TT colection.\n Select TT sent Journal"))
        else:
            query = """
                                        select id from account_journal where default_credit_account_id = 
                                            (select cheque_in_hand_account_id from saleotherexpense where company_id = {} limit 1) limit 1
                                            """.format(self.env.user.company_id.id)
            line_details.journal_id = self._get_journal_id_by_query(query)
        return line_details

    def btn_submit_for_approval(self):
        for rec in self:
            user_company_id = self.env.user.company_id.id
            saleotherexpense = self.env['saleotherexpense']
            fields_get = saleotherexpense.fields_get()
            if 'cheque_in_hand_account_id' in fields_get.keys():
                company_setting_existORnot = self.env['saleotherexpense'].search([('company_id', '=', user_company_id)])
                if company_setting_existORnot:
                    if company_setting_existORnot.cheque_in_hand_account_id:
                        print("write your code here")
                    else:
                        raise ValidationError(_('''Check in hand account is not set for this company!!!'''))
                        return False
                else:
                    raise ValidationError(_('''Journal settings required for this company!!!'''))
                    return False
            else:
                raise ValidationError(_('''Update 'sale_extra_cost' module, Cheque in hand doesn't exists!!!'''))
                return False

        if len(self.batch_payment_line) > 0:
            self.state = 'processing'
            self.entry_by = self.env.user.id
            for line_details in self.batch_payment_line:
                line_details = self.set_journal_id(line_details)
                validation_message = self.check_validation(line_details)
                if not validation_message:
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
                else:
                    raise ValidationError(_(validation_message))
                    return False
        else:
            raise ValidationError(
                _("Add at least one Payment Information"))
            return False

    def update_invoice_residual_amount_for_multiple_reference_typ_collection(self, given_invoice_ids,
                                                                             increase_or_decrease):
        if given_invoice_ids:
            for invoice_id in given_invoice_ids:
                update_query = """update account_move set amount_residual = COALESCE(amount_residual, 0) {} COALESCE((
                                        select sum(ap.amount) from invoice_wise_account_payment_rel amr
                                        inner join account_payment ap on ap.id = amr.payment_id
                                        where amr.invoice_id = {} and ap.state in ('draft', 'sent', 'waiting_for_approval')
                                        and ap.collection_reference = 'multiple_invoice'
                                        and (ap.initial_create_status is null or ap.initial_create_status = false)
                                        group by amr.payment_id
                                    ), 0) where id = {}""".format(increase_or_decrease, invoice_id, invoice_id)
                self._cr.execute(query=update_query)

                update_line_query = """update account_move_line set amount_residual = COALESCE(amount_residual, 0) {} COALESCE((
                                        select sum(ap.amount) from invoice_wise_account_payment_rel amr
                                        inner join account_payment ap on ap.id = amr.payment_id
                                        where amr.invoice_id = {} and ap.state in ('draft', 'sent', 'waiting_for_approval')
                                        and ap.collection_reference = 'multiple_invoice'
                                        and (ap.initial_create_status is null or ap.initial_create_status = false)
                                        group by amr.payment_id
                                    ), 0) where move_id = {} and account_internal_type = 'receivable'""".format(
                    increase_or_decrease, invoice_id, invoice_id)
                self._cr.execute(query=update_line_query)
                self._cr.commit()

    def btn_approve(self):
        for record in self:
            record.state = 'approve'
            record.approved_by = self.env.user.id
            record.approved_date = date.today()

        for payment_line in self.batch_payment_line:
            payment_line.initial_create_status = False
            # if payment_line.state == 'waiting_for_approval':
            AccountMove = self.env['account.move'].with_context(default_type='entry')
            for rec in payment_line:
                payment_line.cih_date = date.today()
                # payment_line.honor_date = self.payment_date
                payment_line.honor_date = payment_line.effective_date

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
                    print(given_invoice_ids)
                    # Has update residual_amount for avoiding multiple_reference invoice value

                    rec.update({
                        'invoice_ids': [(6, 0, given_invoice_ids)],
                    })

                    # moves.date = rec.effective_date
                    moves = AccountMove.create(rec._prepare_payment_moves())

                    for line in moves.invoice_line_ids:
                        line.collection_date = self.payment_date
                    if rec.effective_date:
                        moves.date = rec.effective_date
                    else:
                        moves.date = self.payment_date
                        # moves.date = datetime.now()

                    if (rec.payment_method_id.code in ['tt', 'manual']):
                        if payment_line.collection_reference != 'multiple_invoice':
                            self.update_invoice_residual_amount_for_multiple_reference_typ_collection(given_invoice_ids,
                                                                                                      '-')
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
                        if rec.collection_reference == 'cheque_adjustment':
                            res_amt = rec.amount
                            for dishonor_chq in rec.dishonor_collection_ids:
                                if dishonor_chq.amount < res_amt:
                                    res_amt -= (dishonor_chq.amount - dishonor_chq.dishonor_balance_adjust_amt)
                                    dishonor_chq.dishonor_balance_adjust_amt += (
                                            dishonor_chq.amount - dishonor_chq.dishonor_balance_adjust_amt)
                                else:
                                    dishonor_chq.dishonor_balance_adjust_amt += res_amt
                                    res_amt -= res_amt
                                    # rec.dishonor_balance_adjust_amt -=

                        if payment_line.collection_reference != 'multiple_invoice':
                            self.update_invoice_residual_amount_for_multiple_reference_typ_collection(given_invoice_ids,
                                                                                                      '+')
                    # moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()
                    else:
                        # Update the state / move before performing any reconciliation.
                        for move_line in moves.line_ids:
                            move_line.ref = "Cheque Collection"

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
    						left join account_payment ap on ap.id = amr.payment_id
    						where am.type = 'out_invoice' and am.partner_id = {}
                            and am.state = 'posted'
                            and invoice_payment_state = 'not_paid'
    						and case 
    							when (COALESCE(am.amount_residual, 0) - ( select COALESCE(sum(amount), 0) from account_payment ext_ap where 
    								  	ext_ap.id in (select payment_id from invoice_wise_account_payment_rel ipr where ipr.invoice_id = amr.invoice_id) and
    								 	ext_ap.collection_reference = 'multiple_invoice' and ext_ap.state in ('draft', 'sent', 'waiting_for_approval')
    									and (ext_ap.initial_create_status is null or ext_ap.initial_create_status = false))) <= 0
    								then 
    									false
    								else true
    							end
     						group by am.id
    						order by am.id asc""".format(batch_payment.partner_id.id)

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