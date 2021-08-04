import copy

from odoo import models, fields, api, _
from datetime import datetime, date

from odoo.exceptions import UserError, ValidationError


def formating_list(given_list):
    list = [(5, 0, 0)]
    for item in given_list:
        list.append((0, 0, {
            'id': item['id'],
            'payment_type': item['payment_type'],
            'payment_date': item['payment_date'],
            'name': item['name'],
            'cheque_reference': item['cheque_reference'],
            'effective_date': item['effective_date'],
            'payment_method_id': item['payment_method_id'],
            'partner_id': item['partner_id'],
            'amount': item['amount'],
            'state': item['state'],
            'company_id': 1,
            'journal_id': item['journal_id'],
        }))
    return list


class ChequeTreatment(models.TransientModel):
    _name = 'cheque.treatment'

    state = fields.Selection([('draft', 'Draft'), ('posted', 'Validated'), ('sent', 'Sent'), ('submit_for_approval', 'Submit for approval'), ('dishonored', 'Dishonored'), ('cancelled', 'Cancelled'), ('finished', 'Finished')], string="Status", default='sent')
    cheque_type = fields.Selection([('customer', 'Collection Cheque'), ('supplier', 'Payment Cheque')], string="Cheque Type", default='customer')
    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Date', required=True, default=fields.Date.today)
    cheque_no = fields.Char(string="Cheque No.")
    branch_id = fields.Many2many('res.branch', 'cheque_treatment_branch_rel', 'treatement_id', 'branch_id', string="Branch")

    temp_payment_id = fields.Char(string="Temp Account Payment Ids")

    journal_id = fields.Many2one('account.journal', string='Sending Bank', domain="[('type', '=', 'bank')]")
    sent_date = fields.Date(string='Sending Date', required=True, default=fields.Date.today)
    dishonor_honor_date = fields.Date(string='Honor/Dishonor Date', required=True, default=fields.Date.today)

    draft_payment_line_ids = fields.Many2many('account.payment', 'cheque_treatment_draft_payment_rel', 'account_payment_id',
                                              'draft_payment_line_id', copy=True, string='Cheque', store=False)
    sent_payment_line_ids = fields.Many2many('account.payment', 'cheque_treatment_sent_payment_rel', 'payment_id', 'sent_payment_line_id', copy=True, string='Cheque', store=False)
    dishonored_payment_line_ids = fields.Many2many('account.payment', 'cheque_treatment_dishonored_payment_rel', string='Cheque', store=False, copy=True)
    approve_payment_line_ids = fields.Many2many('account.payment', 'cheque_treatment_approve_payment_rel', string='Cheque', store=False, copy=True)
    dishonor_by_not_responding_line_ids = fields.Many2many('account.payment', 'cheque_treatment_approve_payment_rel', string='Cheque', store=False, copy=True)
    # submit_for_approval_payment_line_ids = fields.Many2many('account.payment', 'cheque_treatment_submit_for_approval_payment_rel', string='Cheque', store=False, copy=True)

    # draft_payment_line_ids = fields.Many2many('account.payment', 'cheque_treatment_draft_payment_rel', 'account_payment_id',
    #                                           'draft_payment_line_id', copy=False, string='Cheque', store=False,
    #                                           default=lambda self: self.load_draft_default())
    # sent_payment_line_ids = fields.Many2many('account.payment', 'cheque_treatment_sent_payment_rel', 'payment_id', 'sent_payment_line_id', copy=False, string='Cheque', default=lambda self: self.load_sent_default())
    # dishonored_payment_line_ids = fields.Many2many('account.payment', 'cheque_treatment_dishonored_payment_rel', string='Cheque', default=lambda self: self.load_dishonored_default())
    # approve_payment_line_ids = fields.Many2many('account.payment', 'cheque_treatment_approve_payment_rel', string='Cheque', default=lambda self: self.load_approve_default())
    # submit_for_approval_payment_line_ids = fields.Many2many('account.payment', 'cheque_treatment_submit_for_approval_payment_rel', string='Cheque', default=lambda self: self.load_submit_for_approval_default())
    sent_btn_trigger = fields.Char(string="Change")
    # submit_for_approval_btn_trigger = fields.Char(string="Change")
    dishonored_btn_trigger = fields.Char(string="Change")
    approved_btn_trigger = fields.Char(string="Change")
    reset_to_draft_btn_trigger = fields.Char(string="Change")
    reset_to_draft_not_response_btn_trigger = fields.Char(string="Change")

    @api.onchange('draft_payment_line_ids')
    def _draft_payment_line_ids_on_change(self):
        self.temp_payment_id = ""

        for payment_line in self.draft_payment_line_ids:
            if payment_line.in_treatment_state:
                payment_line.in_treatment_state = True
                temp_account_payment = self.env['account.payment'].search([('cheque_reference', '=', payment_line.cheque_reference)], limit=1)
                if temp_account_payment:
                    self.temp_payment_id += str(temp_account_payment[0].id) + " , "

    @api.onchange('sent_payment_line_ids')
    def _sent_payment_line_ids_on_change(self):
        self.temp_payment_id = ""

        for payment_line in self.sent_payment_line_ids:
            if payment_line.in_treatment_state:
                payment_line.in_treatment_state = True
                temp_account_payment = self.env['account.payment'].search([('cheque_reference', '=', payment_line.cheque_reference)], limit=1)
                if temp_account_payment:
                    self.temp_payment_id += str(temp_account_payment[0].id) + " , "

    @api.onchange('dishonored_payment_line_ids')
    def _dishonored_payment_line_ids_on_change(self):
        self.temp_payment_id = ""

        for payment_line in self.dishonored_payment_line_ids:
            if payment_line.in_treatment_state:
                payment_line.in_treatment_state = True
                temp_account_payment = self.env['account.payment'].search([('cheque_reference', '=', payment_line.cheque_reference)], limit=1)
                if temp_account_payment:
                    self.temp_payment_id += str(temp_account_payment[0].id) + " , "

    # @api.onchange('submit_for_approval_payment_line_ids')
    # def _submit_for_approval_payment_line_ids_on_change(self):
    #     self.temp_payment_id = ""
    #
    #     for payment_line in self.submit_for_approval_payment_line_ids:
    #         if payment_line.in_treatment_state:
    #             payment_line.in_treatment_state = True
    #             temp_account_payment = self.env['account.payment'].search([('cheque_reference', '=', payment_line.cheque_reference)], limit=1)
    #             if temp_account_payment:
    #                 self.temp_payment_id += str(temp_account_payment[0].id) + " , "

    # @api.model
    # def load_dishonored_default(self):
    #     if self.date_start:
    #         query = """
    #                                     select * from account_payment where state = 'dishonored' and effective_date >= TO_DATE('{}', 'YYYY-MM-DD') and effective_date <= TO_DATE('{}', 'YYYY-MM-DD') """.format(
    #             self.date_start.strftime('%Y-%m-%d'), self.date_end.strftime('%Y-%m-%d'))
    #     else:
    #         query = """
    #                         select * from account_payment where state = 'dishonored' and effective_date >= TO_DATE('{}', 'YYYY-MM-DD') and effective_date <= TO_DATE('{}', 'YYYY-MM-DD') """.format(datetime.today().strftime('%Y-%m-%d'), datetime.today().strftime('%Y-%m-%d'))
    #
    #     if self.cheque_type:
    #         query += """
    #              and partner_type = '{}'
    #                     """.format(self.cheque_type)
    #     else:
    #         query += """
    #                  and partner_type = 'customer'
    #                 """
    #
    #     if self.cheque_no:
    #         query += """
    #              and check_number like '{}%'
    #                     """.format(self.cheque_no)
    #
    #     if self.branch_id:
    #         query += """
    #              and branch_id = {}
    #                     """.format(self.branch_id)
    #
    #     self._cr.execute(query=query)
    #     payment_list = self._cr.dictfetchall()
    #
    #     return payment_list
    #
    # @api.model
    # def load_approve_default(self):
    #     if self.date_start:
    #         query = """
    #                                     select * from account_payment where state = 'posted' and effective_date >= TO_DATE('{}', 'YYYY-MM-DD') and effective_date <= TO_DATE('{}', 'YYYY-MM-DD') """.format(
    #             self.date_start.strftime('%Y-%m-%d'), self.date_end.strftime('%Y-%m-%d'))
    #     else:
    #         query = """
    #                         select * from account_payment where state = 'posted' and effective_date >= TO_DATE('{}', 'YYYY-MM-DD') and effective_date <= TO_DATE('{}', 'YYYY-MM-DD') """.format(datetime.today().strftime('%Y-%m-%d'), datetime.today().strftime('%Y-%m-%d'))
    #
    #     if self.cheque_type:
    #         query += """
    #              and partner_type = '{}'
    #                     """.format(self.cheque_type)
    #     else:
    #         query += """
    #                  and partner_type = 'customer'
    #                 """
    #
    #     if self.cheque_no:
    #         query += """
    #              and check_number like '{}%'
    #                     """.format(self.cheque_no)
    #
    #     if self.branch_id:
    #         query += """
    #              and branch_id = {}
    #                     """.format(self.branch_id)
    #
    #     self._cr.execute(query=query)
    #     payment_list = self._cr.dictfetchall()
    #
    #     return payment_list
    #
    # @api.model
    # def load_submit_for_approval_default(self):
    #     if self.date_start:
    #         query = """
    #                                     select * from account_payment where state = 'waiting_for_approval' and effective_date >= TO_DATE('{}', 'YYYY-MM-DD') and effective_date <= TO_DATE('{}', 'YYYY-MM-DD') """.format(
    #             self.date_start.strftime('%Y-%m-%d'), self.date_end.strftime('%Y-%m-%d'))
    #     else:
    #         query = """
    #                         select * from account_payment where state = 'waiting_for_approval' and effective_date >= TO_DATE('{}', 'YYYY-MM-DD') and effective_date <= TO_DATE('{}', 'YYYY-MM-DD') """.format(datetime.today().strftime('%Y-%m-%d'), datetime.today().strftime('%Y-%m-%d'))
    #
    #     if self.cheque_type:
    #         query += """
    #              and partner_type = '{}'
    #                     """.format(self.cheque_type)
    #     else:
    #         query += """
    #                  and partner_type = 'customer'
    #                 """
    #
    #     if self.cheque_no:
    #         query += """
    #              and check_number like '{}%'
    #                     """.format(self.cheque_no)
    #
    #     if self.branch_id:
    #         query += """
    #              and branch_id = {}
    #                     """.format(self.branch_id)
    #
    #     self._cr.execute(query=query)
    #     payment_list = self._cr.dictfetchall()
    #
    #     return payment_list
    #
    # @api.model
    # def load_draft_default(self):
    #     if self.date_start:
    #         query = """
    #                                     select * from account_payment where state = 'draft' and effective_date >= TO_DATE('{}', 'YYYY-MM-DD') and effective_date <= TO_DATE('{}', 'YYYY-MM-DD') """.format(
    #             self.date_start.strftime('%Y-%m-%d'), self.date_end.strftime('%Y-%m-%d'))
    #     else:
    #         query = """
    #                         select * from account_payment where state = 'draft' and effective_date >= TO_DATE('{}', 'YYYY-MM-DD') and effective_date <= TO_DATE('{}', 'YYYY-MM-DD') """.format(
    #             datetime.today().strftime('%Y-%m-%d'), datetime.today().strftime('%Y-%m-%d'))
    #
    #     if self.cheque_type:
    #         query += """
    #              and partner_type = '{}'
    #                     """.format(self.cheque_type)
    #     else:
    #         query += """
    #                  and partner_type = 'customer'
    #                 """
    #
    #     if self.cheque_no:
    #         query += """
    #              and check_number like '{}%'
    #                     """.format(self.cheque_no)
    #
    #     if self.branch_id:
    #         query += """
    #              and branch_id = {}
    #                     """.format(self.branch_id)
    #
    #     self._cr.execute(query=query)
    #     payment_list = self._cr.dictfetchall()
    #
    #     return payment_list
    #
    # @api.model
    # def load_sent_default(self):
    #     # list = []
    #     list = [(5, 0, 0)]
    #     if self.date_start:
    #         query = """
    #                                     select * from account_payment where state = 'sent' and effective_date >= TO_DATE('{}', 'YYYY-MM-DD') and effective_date <= TO_DATE('{}', 'YYYY-MM-DD') """.format(
    #             self.date_start.strftime('%Y-%m-%d'), self.date_end.strftime('%Y-%m-%d'))
    #     else:
    #         query = """
    #                         select * from account_payment where state = 'sent' and effective_date >= TO_DATE('{}', 'YYYY-MM-DD') and effective_date <= TO_DATE('{}', 'YYYY-MM-DD') """.format(datetime.today().strftime('%Y-%m-%d'), datetime.today().strftime('%Y-%m-%d'))
    #
    #     # if self.state:
    #     #     query += """
    #     #          and state = '{}'
    #     #                 """.format(self.state)
    #     # else:
    #     #     query += """
    #     #              and state = 'posted'
    #     #             """
    #
    #     if self.cheque_type:
    #         query += """
    #              and partner_type = '{}'
    #                     """.format(self.cheque_type)
    #     else:
    #         query += """
    #                  and partner_type = 'customer'
    #                 """
    #
    #     if self.cheque_no:
    #         query += """
    #              and check_number like '{}%'
    #                     """.format(self.cheque_no)
    #
    #     if self.branch_id:
    #         query += """
    #              and branch_id = {}
    #                     """.format(self.branch_id)
    #
    #     self._cr.execute(query=query)
    #     payment_list = self._cr.dictfetchall()
    #
    #     # if not self.state:
    #     #     payment_list = self.env['account.payment'].search([('effective_date', '>=', self.date_start), ('effective_date', '<=', self.date_end), ('state', '=', 'sent')])
    #     # else:
    #     # payment_list = self.env['account.payment'].search([('state', '=', 'posted')])
    #     # for item in payment_list:
    #     #     list.append((0, 0, {
    #     #         'id': item[0],
    #     #         'payment_type': item[6],
    #     #         'payment_date': item[12],
    #     #         'name': item[1],
    #     #         'payment_method_id': item[7],
    #     #         'partner_id': item[9],
    #     #         'amount': item[10],
    #     #         'state': item[5],
    #     #         'company_id': item[28],
    #     #         'journal_id': item[14],
    #     #     }))
    #     # for item in payment_list:
    #     #     list.append({
    #     #         'id': item['id'],
    #     #         'payment_type': item['payment_type'],
    #     #         'payment_date': item['payment_date'],
    #     #         'name': item['name'],
    #     #         'cheque_reference': item['cheque_reference'],
    #     #         'payment_method_id': item['payment_method_id'],
    #     #         'partner_id': item['partner_id'],
    #     #         'amount': item['amount'],
    #     #         'state': item['state'],
    #     #         'company_id': 1,
    #     #         'journal_id': item['journal_id'],
    #     #     })
    #
    #     # self.payment_line_ids = list
    #     # self.payment_line_ids = payment_list
    #     # self.payment_line_ids = item_list
    #     return payment_list
    #
    # def load_cheque_list(self):
    #     print("Load All")
    #     # for rec in self:
    #     #     list = []
    #     #     # list = [(5, 0, 0)]
    #     #
    #     #     if self.date_start:
    #     #         query = """
    #     #                                     select * from account_payment where effective_date >= TO_DATE('{}', 'YYYY-MM-DD') and effective_date <= TO_DATE('{}', 'YYYY-MM-DD') """.format(
    #     #             self.date_start.strftime('%Y-%m-%d'), self.date_end.strftime('%Y-%m-%d'))
    #     #     else:
    #     #         query = """
    #     #                         select * from account_payment where effective_date >= TO_DATE('{}', 'YYYY-MM-DD') and effective_date <= TO_DATE('{}', 'YYYY-MM-DD') """.format(
    #     #             datetime.today().strftime('%Y-%m-%d'), datetime.today().strftime('%Y-%m-%d'))
    #     #
    #     #     if self.state:
    #     #         query += """
    #     #                      and state = '{}'
    #     #                             """.format(self.state)
    #     #     else:
    #     #         query += """
    #     #                          and state = 'sent'
    #     #                         """
    #     #
    #     #     if self.cheque_type:
    #     #         query += """
    #     #                      and partner_type = '{}'
    #     #                             """.format(self.cheque_type)
    #     #     else:
    #     #         query += """
    #     #                          and partner_type = 'customer'
    #     #                         """
    #     #
    #     #     if self.cheque_no:
    #     #         query += """
    #     #                      and check_number like '{}%'
    #     #                             """.format(self.cheque_no)
    #     #
    #     #     if self.branch_id:
    #     #         query += """
    #     #                      and branch_id = {}
    #     #                             """.format(self.branch_id)
    #     #
    #     #     self._cr.execute(query=query)
    #     #     payment_list = self._cr.dictfetchall()
    #     #
    #     #     # if not rec.state:
    #     #     #     payment_list = self.env['account.payment'].search([('state', '=', 'sent')])
    #     #     # else:
    #     #     #     payment_list = self.env['account.payment'].search([('state', '=', rec.state)])
    #     #     # payment_list = self.env['account.payment'].search([('state', '=', 'posted')])
    #     #     for item in payment_list:
    #     #         list.append({
    #     #             'id': item.id,
    #     #             'payment_type': item.payment_type,
    #     #             'payment_date': item.payment_date,
    #     #             'name': item.name,
    #     #             'payment_method_id': item.payment_method_id.id,
    #     #             'partner_id': item.partner_id.id,
    #     #             'amount': item.amount,
    #     #             'state': item.state,
    #     #             'company_id': item.company_id.id,
    #     #             'journal_id': item.journal_id.id,
    #     #         })
    #     #     rec.payment_line_ids = payment_list
    #     # # self.payment_line_ids = [(6, 0, list)]
    #     # # self.payment_line_ids = payment_list
    #     # # return {'value': {'payment_line_ids': list}}
    #     # return self
    #     # # load_default()
    #     # # print("here")
    #     # # val = "sads"

    def generate_journal_entry_for_bank_issue(self, payment, credit_journal_id, debit_journal_id):
        print("sdfsf")
        all_move_vals = []
        company_currency = payment.company_id.currency_id
        move_names = payment.move_name.split(payment._get_move_name_transfer_separator()) if payment.move_name else None

        # Compute amounts.
        write_off_amount = payment.payment_difference_handling == 'reconcile' and -payment.payment_difference or 0.0
        if payment.payment_type in ('outbound', 'transfer'):
            counterpart_amount = payment.amount
            liquidity_line_account = payment.journal_id.default_debit_account_id
        else:
            counterpart_amount = -payment.amount
            liquidity_line_account = payment.journal_id.default_credit_account_id

        # Manage currency.
        if payment.currency_id == company_currency:
            # Single-currency.
            balance = counterpart_amount
            write_off_balance = write_off_amount
            counterpart_amount = write_off_amount = 0.0
            currency_id = False
        else:
            # Multi-currencies.
            balance = payment.currency_id._convert(counterpart_amount, company_currency, payment.company_id,
                                                   payment.payment_date)
            write_off_balance = payment.currency_id._convert(write_off_amount, company_currency, payment.company_id,
                                                             payment.payment_date)
            currency_id = payment.currency_id.id

        # Manage custom currency on journal for liquidity line.
        if payment.journal_id.currency_id and payment.currency_id != payment.journal_id.currency_id:
            # Custom currency on journal.
            if payment.journal_id.currency_id == company_currency:
                # Single-currency
                liquidity_line_currency_id = False
            else:
                liquidity_line_currency_id = payment.journal_id.currency_id.id
            liquidity_amount = company_currency._convert(
                balance, payment.journal_id.currency_id, payment.company_id, payment.payment_date)
        else:
            # Use the payment currency.
            liquidity_line_currency_id = currency_id
            liquidity_amount = counterpart_amount

        # Compute 'name' to be used in receivable/payable line.
        rec_pay_line_name = ''
        if payment.payment_type == 'transfer':
            rec_pay_line_name = payment.name
        else:
            if payment.partner_type == 'customer':
                if payment.payment_type == 'inbound':
                    rec_pay_line_name += _("Customer Payment")
                elif payment.payment_type == 'outbound':
                    rec_pay_line_name += _("Customer Credit Note")
            elif payment.partner_type == 'supplier':
                if payment.payment_type == 'inbound':
                    rec_pay_line_name += _("Vendor Credit Note")
                elif payment.payment_type == 'outbound':
                    rec_pay_line_name += _("Vendor Payment")
            if payment.invoice_ids:
                rec_pay_line_name += ': %s' % ', '.join(payment.invoice_ids.mapped('name'))

        # Compute 'name' to be used in liquidity line.
        if payment.payment_type == 'transfer':
            liquidity_line_name = _('Transfer to %s') % payment.destination_journal_id.name
        else:
            liquidity_line_name = payment.name

        # ==== 'inbound' / 'outbound' ====

        move_vals = {
            'date': payment.payment_date,
            'ref': payment.communication,
            'journal_id': payment.journal_id.id,
            'currency_id': payment.journal_id.currency_id.id or payment.company_id.currency_id.id,
            'partner_id': False,
            'line_ids': [
                # Receivable / Payable / Transfer line.
                (0, 0, {
                    'name': rec_pay_line_name,
                    'amount_currency': counterpart_amount + write_off_amount if currency_id else 0.0,
                    'currency_id': currency_id,
                    'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                    'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
                    'date_maturity': payment.payment_date,
                    'partner_id': payment.partner_id.commercial_partner_id.id,
                    'account_id': credit_journal_id.default_credit_account_id.id,
                    'payment_id': payment.id,
                }),
                # Liquidity line.
                (0, 0, {
                    'name': liquidity_line_name,
                    'amount_currency': -liquidity_amount if liquidity_line_currency_id else 0.0,
                    'currency_id': liquidity_line_currency_id,
                    'debit': balance < 0.0 and -balance or 0.0,
                    'credit': balance > 0.0 and balance or 0.0,
                    'date_maturity': payment.payment_date,
                    'partner_id': payment.partner_id.commercial_partner_id.id,
                    'account_id': debit_journal_id.default_debit_account_id.id,
                    'payment_id': payment.id,
                }),
            ],
        }
        if move_names:
            move_vals['name'] = move_names[0]

        all_move_vals.append(move_vals)
        return all_move_vals

    @api.onchange('sent_btn_trigger')
    def _onchange_sent_btn_trigger(self):
        if self.temp_payment_id:
            payment_id_list = self.temp_payment_id.split(" , ")
            payment_id_list.remove('')
            payment_list = self.env['account.payment'].search([('id', 'in', payment_id_list)])

            for payment_line in payment_list:
                if payment_line.state == 'draft':
                    payment_line.journal_id = self.journal_id
                    # payment_line.draft_account_move_id.journal_id = self.journal_id
                    # payment_line.state = 'sent'
                    # payment_line.sent_date = date.today()
                    payment_line.sent_date = self.sent_date

                    # Start For Bank Issue journal Passing
                    AccountMove = self.env['account.move'].with_context(default_type='entry')
                    moves = AccountMove.create(self.generate_journal_entry_for_bank_issue(payment_line, payment_line.draft_account_move_id.journal_id, self.journal_id))
                    payment_line.bank_issue_account_move_id = moves.id
                    moves.date = payment_line.effective_date
                    # End For Bank Issue journal Passing


            self.submit_for_approval()
            self.page_change_event()

    def submit_for_approval(self):
        payment_id_list = self.temp_payment_id.split(" , ")
        payment_id_list.remove('')
        payment_list = self.env['account.payment'].search([('id', 'in', payment_id_list)])
        # print(tmp_payment_id_array)
        # query = """
        #                             select account_payment_id from cheque_treatment_sent_payment_rel"""
        # self._cr.execute(query=query)
        # payment_id_list = self._cr.fetchall()

        # for payment_line in self.sent_payment_line_ids:
        for payment_line in payment_list:
            print(payment_line)
            if payment_line.state == 'draft':
                logged_user = self._uid
                print(logged_user)
                get_logged_user_branch = self.env['res.users'].search([('id', '=', self._uid)]).branch_id
                print(get_logged_user_branch.id)
                _default_warehouse = self.env.user.context_default_warehouse_id.name
                approved_setting = self.env['customer.payment.approval'].search([])
                if approved_setting.approve_customer_payment:
                    payment_line.state = 'waiting_for_approval'
                    partner_ids = []
                    display_message = 'An customer payment is posted on the "waiting for approval" state. Please approve it.'
                    for approver in approved_setting.customer_payment_approver_ids:
                        get_approval_user_branch = self.env['res.users'].search(
                            [('id', '=', approver.id)]).branch_id
                        print(get_approval_user_branch.id)
                        # print('Salesman Default warehouse', salesman_default_warehouse)
                        # print('Approver Default warehouse', approver.context_default_warehouse_id.name)
                        if get_logged_user_branch.id == get_approval_user_branch.id:
                            # if approver.context_default_warehouse_id.name == _default_warehouse:
                            approver.notify_info(message=display_message)
                            partner_ids.append(
                                self.env['res.partner'].search([('name', 'ilike', approver.name)], limit=1).id)

                    # sale_order = self.env['sale.order'].browse(self.env.context.get('active_ids'))
                    payment_line.message_post(body=display_message, subtype='mt_note', partner_ids=partner_ids)
                else:
                    payment_line.state = 'sent'

    # @api.onchange('submit_for_approval_btn_trigger')
    # def _onchange_submit_for_approval_btn_trigger(self):
    #     if self.temp_payment_id:
    #         payment_id_list = self.temp_payment_id.split(" , ")
    #         payment_id_list.remove('')
    #         payment_list = self.env['account.payment'].search([('id', 'in', payment_id_list)])
    #         # print(tmp_payment_id_array)
    #         # query = """
    #         #                             select account_payment_id from cheque_treatment_sent_payment_rel"""
    #         # self._cr.execute(query=query)
    #         # payment_id_list = self._cr.fetchall()
    #
    #         # for payment_line in self.sent_payment_line_ids:
    #         for payment_line in payment_list:
    #             print(payment_line)
    #             if payment_line.state == 'sent':
    #                 logged_user = self._uid
    #                 print(logged_user)
    #                 get_logged_user_branch = self.env['res.users'].search([('id', '=', self._uid)]).branch_id
    #                 print(get_logged_user_branch.id)
    #                 _default_warehouse = self.env.user.context_default_warehouse_id.name
    #                 approved_setting = self.env['customer.payment.approval'].search([])
    #                 if approved_setting.approve_customer_payment:
    #                     payment_line.state = 'waiting_for_approval'
    #                     partner_ids = []
    #                     display_message = 'An customer payment is posted on the "waiting for approval" state. Please approve it.'
    #                     for approver in approved_setting.customer_payment_approver_ids:
    #                         get_approval_user_branch = self.env['res.users'].search(
    #                             [('id', '=', approver.id)]).branch_id
    #                         print(get_approval_user_branch.id)
    #                         # print('Salesman Default warehouse', salesman_default_warehouse)
    #                         # print('Approver Default warehouse', approver.context_default_warehouse_id.name)
    #                         if get_logged_user_branch.id == get_approval_user_branch.id:
    #                             # if approver.context_default_warehouse_id.name == _default_warehouse:
    #                             approver.notify_info(message=display_message)
    #                             partner_ids.append(
    #                                 self.env['res.partner'].search([('name', 'ilike', approver.name)], limit=1).id)
    #
    #                     # sale_order = self.env['sale.order'].browse(self.env.context.get('active_ids'))
    #                     payment_line.message_post(body=display_message, subtype='mt_note', partner_ids=partner_ids)
    #                 else:
    #                     payment_line.state = 'sent'
    #
    #         self.page_change_event()

    @api.onchange('approved_btn_trigger')
    def _onchange_approved_btn_trigger(self):
        if self.temp_payment_id:
            payment_id_list = self.temp_payment_id.split(" , ")
            payment_id_list.remove('')
            payment_list = self.env['account.payment'].search([('id', 'in', payment_id_list)])

            for payment_line in payment_list:
                if payment_line.state == 'waiting_for_approval':
                    if payment_line.collection_reference == 'cheque_adjustment':
                        for dishonor_cheq in payment_line.dishonor_collection_ids:
                            dishonor_cheq.dishonor_balance_adjust_amt += payment_line.amount
                    # AccountMove = self.env['account.move'].with_context(default_type='entry')
                    for rec in payment_line:
                        # payment_line.honor_date = date.today()
                        payment_line.honor_date = self.dishonor_honor_date
                        if rec.state != 'waiting_for_approval':
                            raise UserError(_("Only a waiting for approval payment can be posted."))

                        if any(inv.state != 'posted' for inv in rec.invoice_ids):
                            raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

                        # moves = AccountMove.create(rec._prepare_payment_moves())
                        moves = self.env['account.move'].search([('id', '=', rec.draft_account_move_id.id)])
                        bank_issue_moves = self.env['account.move'].search([('id', '=', rec.bank_issue_account_move_id.id)])
                        # moves.journal_id = rec.draft_account_move_id.id

                        moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()
                        bank_issue_moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()

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

            self.page_change_event()

    # @api.onchange('approved_btn_trigger')
    # def _onchange_approved_btn_trigger(self):
    #     if self.temp_payment_id:
    #         payment_id_list = self.temp_payment_id.split(" , ")
    #         payment_id_list.remove('')
    #         payment_list = self.env['account.payment'].search([('id', 'in', payment_id_list)])
    #         rest_amount = 0
    #
    #         for payment_line in payment_list:
    #             if payment_line.state == 'waiting_for_approval':
    #                 AccountMove = self.env['account.move'].with_context(default_type='entry')
    #                 for rec in payment_line:
    #                     # payment_line.honor_date = date.today()
    #                     payment_line.honor_date = self.dishonor_honor_date
    #                     rest_amount = payment_line.amount
    #                     if rec.state != 'waiting_for_approval':
    #                         raise UserError(_("Only a waiting for approval payment can be posted."))
    #
    #                     if any(inv.state != 'posted' for inv in rec.invoice_ids):
    #                         raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))
    #
    #                     # keep the name in case of a payment reset to draft
    #                     if not rec.name:
    #                         # Use the right sequence to set the name
    #                         if rec.payment_type == 'transfer':
    #                             sequence_code = 'account.payment.transfer'
    #                         else:
    #                             if rec.partner_type == 'customer':
    #                                 if rec.payment_type == 'inbound':
    #                                     sequence_code = 'account.payment.customer.invoice'
    #                                 if rec.payment_type == 'outbound':
    #                                     sequence_code = 'account.payment.customer.refund'
    #                             if rec.partner_type == 'supplier':
    #                                 if rec.payment_type == 'inbound':
    #                                     sequence_code = 'account.payment.supplier.refund'
    #                                 if rec.payment_type == 'outbound':
    #                                     sequence_code = 'account.payment.supplier.invoice'
    #                         rec.name = self.env['ir.sequence'].next_by_code(sequence_code,
    #                                                                         sequence_date=rec.payment_date)
    #                         if not rec.name and rec.payment_type != 'transfer':
    #                             raise UserError(
    #                                 _("You have to define a sequence for %s in your company.") % (sequence_code,))
    #
    #                     # # start with collection reference
    #                     #
    #                     # if rec.collection_reference == 'advance_collection':
    #                     #     moves = AccountMove.create(rec._prepare_payment_moves())
    #                     #     moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()
    #                     #
    #                     # if rec.collection_reference == 'multiple_invoice':
    #                     #     for invoice_move in rec.payment_invoice_ids:
    #                     #         moves = invoice_move
    #                     #         # multiple_moves = self.env['account.move'].search([('id', '=', invoice.invoice_id)], limit=1)
    #                     #         data = moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()
    #                     #         print("posted")
    #                     #
    #                     #     # moves = AccountMove.create(rec._prepare_payment_moves())
    #                     #
    #                     #
    #                     #
    #                     # # Update the state / move before performing any reconciliation.
    #                     # move_name = payment_line._get_move_name_transfer_separator().join(moves.mapped('name'))
    #                     # rec.write({'state': 'posted', 'move_name': move_name})
    #                     #
    #                     # if rec.payment_type in ('inbound', 'outbound'):
    #                     #     # ==== 'inbound' / 'outbound' ====
    #                     #     if rec.invoice_ids:
    #                     #         (moves[0] + rec.invoice_ids).line_ids \
    #                     #             .filtered(
    #                     #             lambda line: not line.reconciled and line.account_id == rec.destination_account_id) \
    #                     #             .reconcile()
    #                     # elif rec.payment_type == 'transfer':
    #                     #     # ==== 'transfer' ====
    #                     #     moves.mapped('line_ids') \
    #                     #         .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id) \
    #                     #         .reconcile()
    #                     #
    #                         given_invoice_ids = self.get_given_invoices(rec)
    #                         # if rec.collection_reference == 'multiple_invoice':
    #                         #     for given_invoice in rec.payment_invoice_ids:
    #                         #         given_invoice_ids.append(given_invoice.id)
    #                         rec.update({
    #                             'invoice_ids': [(6, 0, given_invoice_ids)],
    #                         })
    #
    #                         moves = AccountMove.create(rec._prepare_payment_moves())
    #                         moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()
    #
    #                         # Update the state / move before performing any reconciliation.
    #                         move_name = payment_line._get_move_name_transfer_separator().join(moves.mapped('name'))
    #                         rec.write({'state': 'posted', 'move_name': move_name})
    #
    #                         if rec.payment_type in ('inbound', 'outbound'):
    #                             # ==== 'inbound' / 'outbound' ====
    #                             if rec.invoice_ids:
    #                                 (moves[0] + rec.invoice_ids).line_ids \
    #                                     .filtered(
    #                                     lambda line: not line.reconciled and line.account_id == rec.destination_account_id) \
    #                                     .reconcile()
    #                         elif rec.payment_type == 'transfer':
    #                             # ==== 'transfer' ====
    #                             moves.mapped('line_ids') \
    #                                 .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id) \
    #                                 .reconcile()
    #
    #                     # flag_state = 'finished'
    #                     # for payment_line in payment_list:
    #                     #     if (payment_line.state != 'posted'):
    #                     #         flag_state = 'processing'
    #                     #         break
    #
    #                     # # end with collection reference
    #
    #             #         moves = AccountMove.create(rec._prepare_payment_moves())
    #             #         moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()
    #             #
    #             #         # Update the state / move before performing any reconciliation.
    #             #         move_name = payment_line._get_move_name_transfer_separator().join(moves.mapped('name'))
    #             #         rec.write({'state': 'posted', 'move_name': move_name})
    #             #
    #             #         if rec.payment_type in ('inbound', 'outbound'):
    #             #             # ==== 'inbound' / 'outbound' ====
    #             #             if rec.invoice_ids:
    #             #                 (moves[0] + rec.invoice_ids).line_ids \
    #             #                     .filtered(
    #             #                     lambda line: not line.reconciled and line.account_id == rec.destination_account_id) \
    #             #                     .reconcile()
    #             #         elif rec.payment_type == 'transfer':
    #             #             # ==== 'transfer' ====
    #             #             moves.mapped('line_ids') \
    #             #                 .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id) \
    #             #                 .reconcile()
    #             #
    #             # flag_state = 'finished'
    #             # for payment_line in payment_list:
    #             #     if (payment_line.state != 'posted'):
    #             #         flag_state = 'processing'
    #             #         break
    #
    #         self.page_change_event()

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
        return given_invoice_ids

    @api.onchange('dishonored_btn_trigger')
    def _onchange_dishonored_btn_trigger(self):
        if self.temp_payment_id:
            payment_id_list = self.temp_payment_id.split(" , ")
            payment_id_list.remove('')
            payment_list = self.env['account.payment'].search([('id', 'in', payment_id_list)])

            for payment_line in payment_list:
                self.dishonor_payment(payment_line)
                    # revrse account move which was in draft state end

            self.page_change_event()

    def dishonor_payment(self, payment_line):
        if payment_line.state == 'waiting_for_approval':
            # payment_line.dishonor_date = date.today()

            payment_line.dishonor_date = date.today() if self.dishonor_honor_date else date.today()
            payment_line.state = 'dishonored'
            payment_line.dishonor_count = payment_line.dishonor_count + 1
            get_partner = self.env['res.partner'].browse(payment_line.partner_id.id)
            get_partner.update({
                'sale_not_allow': True
            })

            # revrse account move which was in draft state start
            if payment_line.draft_account_move_id:
                move_reversal = self.env['account.move.reversal'].with_context(active_model="account.move", active_ids=payment_line.draft_account_move_id.ids).create({
                    'date': date.today() if self.dishonor_honor_date else date.today(),
                    'reason': 'Cheque has dishonored',
                    'refund_method': 'refund',
                })
                reversal = move_reversal.reverse_moves()
            # revrse account move which was in draft state end
            # revrse account move which was in draft state in Issue Bank start
            if payment_line.bank_issue_account_move_id:
                issue_bank_move_reversal = self.env['account.move.reversal'].with_context(active_model="account.move", active_ids=payment_line.bank_issue_account_move_id.ids).create({
                    'date': date.today() if self.dishonor_honor_date else date.today(),
                    'reason': 'Cheque has dishonored',
                    'refund_method': 'refund',
                })
                reversal = issue_bank_move_reversal.reverse_moves()
                # revrse account move which was in draft state in Issue Bank End

    def reset_to_draft(self):
        if self.temp_payment_id:
            payment_id_list = self.temp_payment_id.split(" , ")
            payment_id_list.remove('')
            payment_list = self.env['account.payment'].search([('id', 'in', payment_id_list)])

            for payment_line in payment_list:
                if (payment_line.state == 'dishonored') or (payment_line.state == 'cancelled') or (
                        payment_line.state == 'reconciled'):
                    # # Previous dishonor treatment start
                    # moves = payment_line.mapped('move_line_ids.move_id')
                    # moves.filtered(lambda move: move.state == 'posted').button_draft()
                    # moves.with_context(force_delete=True).unlink()
                    # payment_line.state = 'draft'
                    # payment_line.invoice_ids = False
                    # # Previous dishonor treatment End
                    AccountMove = self.env['account.move'].with_context(default_type='entry')
                    payment_line.honor_date = date.today()
                    payment_line.state = 'draft'
                    # rest_amount = payment_line.amount
                    # if rec.state != 'waiting_for_approval':
                    #     raise UserError(_("Only a waiting for approval payment can be posted."))

                    if any(inv.state != 'posted' for inv in payment_line.invoice_ids):
                        raise ValidationError(
                            _("The payment cannot be processed because the invoice is not open!"))

                    # keep the name in case of a payment reset to draft
                    # if not payment_line.name:
                    # Use the right sequence to set the name
                    if payment_line.payment_type == 'transfer':
                        sequence_code = 'account.payment.transfer'
                    else:
                        if payment_line.partner_type == 'customer':
                            if payment_line.payment_type == 'inbound':
                                sequence_code = 'account.payment.customer.invoice'
                            if payment_line.payment_type == 'outbound':
                                sequence_code = 'account.payment.customer.refund'
                        if payment_line.partner_type == 'supplier':
                            if payment_line.payment_type == 'inbound':
                                sequence_code = 'account.payment.supplier.refund'
                            if payment_line.payment_type == 'outbound':
                                sequence_code = 'account.payment.supplier.invoice'
                    payment_line.name = self.env['ir.sequence'].next_by_code(sequence_code,
                                                                    sequence_date=payment_line.payment_date)
                    if not payment_line.name and payment_line.payment_type != 'transfer':
                        raise UserError(
                            _("You have to define a sequence for %s in your company.") % (sequence_code,))

                    # given_invoice_ids = self.get_given_invoices(payment_line)
                    #
                    # payment_line.update({
                    #     'invoice_ids': [(6, 0, given_invoice_ids)],
                    # })

                    # moves.date = rec.effective_date
                    payment_line.journal_id = self.get_draft_journal_id()
                    moves = AccountMove.create(payment_line._prepare_payment_moves())
                    moves.date = date.today()
                    move_name = payment_line._get_move_name_transfer_separator().join(moves.mapped('name'))
                    payment_line.write({'state': 'draft', 'move_name': move_name, 'draft_account_move_id': moves.id})

            self.page_change_event()

    def get_draft_journal_id(self):
        query = """
                select id from account_journal where default_credit_account_id = 
                    (select cheque_in_hand_account_id from saleotherexpense where company_id = {} limit 1) limit 1
                    """.format(self.env.user.company_id.id)
        self._cr.execute(query=query)
        query_result = self._cr.fetchall()
        if query_result:
            return query_result[0][0]

    @api.onchange('reset_to_draft_btn_trigger')
    def _onchange_reset_to_draft_btn_trigger(self):
        self.reset_to_draft()

    @api.onchange('reset_to_draft_not_response_btn_trigger')
    def _onchange_reset_to_draft_not_response_btn_trigger(self):
        self.reset_to_draft()

    # def btn_sent(self):
    #     if self.temp_payment_id:
    #         payment_id_list = self.temp_payment_id.split(" , ")
    #         payment_id_list.remove('')
    #         payment_list = self.env['account.payment'].search([('id', 'in', payment_id_list)])
    #
    #         for payment_line in payment_list:
    #             if payment_line.state == 'draft':
    #                 payment_line.state = 'sent'
    #                 payment_line.sent_date = date.today()
    #
    #
    #     print(self)
    #     # for payment_line in self.batch_payment_line:
    #     #     if payment_line.state == 'draft':
    #     #         payment_line.state = 'sent'
    #     #         payment_line.sent_date=date.today()
    #
    # def btn_submit_for_approval(self):
    #     if self.temp_payment_id:
    #         payment_id_list = self.temp_payment_id.split(" , ")
    #         payment_id_list.remove('')
    #         payment_list = self.env['account.payment'].search([('id', 'in', payment_id_list)])
    #         # print(tmp_payment_id_array)
    #         # query = """
    #         #                             select account_payment_id from cheque_treatment_sent_payment_rel"""
    #         # self._cr.execute(query=query)
    #         # payment_id_list = self._cr.fetchall()
    #
    #         # for payment_line in self.sent_payment_line_ids:
    #         for payment_line in payment_list:
    #             print(payment_line)
    #             if payment_line.state == 'sent':
    #                 logged_user = self._uid
    #                 print(logged_user)
    #                 get_logged_user_branch = self.env['res.users'].search([('id', '=', self._uid)]).branch_id
    #                 print(get_logged_user_branch.id)
    #                 _default_warehouse = self.env.user.context_default_warehouse_id.name
    #                 approved_setting = self.env['customer.payment.approval'].search([])
    #                 if approved_setting.approve_customer_payment:
    #                     payment_line.state = 'waiting_for_approval'
    #                     partner_ids = []
    #                     display_message = 'An customer payment is posted on the "waiting for approval" state. Please approve it.'
    #                     for approver in approved_setting.customer_payment_approver_ids:
    #                         get_approval_user_branch = self.env['res.users'].search([('id', '=', approver.id)]).branch_id
    #                         print(get_approval_user_branch.id)
    #                         # print('Salesman Default warehouse', salesman_default_warehouse)
    #                         # print('Approver Default warehouse', approver.context_default_warehouse_id.name)
    #                         if get_logged_user_branch.id == get_approval_user_branch.id:
    #                             # if approver.context_default_warehouse_id.name == _default_warehouse:
    #                             approver.notify_info(message=display_message)
    #                             partner_ids.append(
    #                                 self.env['res.partner'].search([('name', 'ilike', approver.name)], limit=1).id)
    #
    #                     # sale_order = self.env['sale.order'].browse(self.env.context.get('active_ids'))
    #                     payment_line.message_post(body=display_message, subtype='mt_note', partner_ids=partner_ids)
    #                 else:
    #                     payment_line.state = 'sent'
    #
    #         # for payment_line in self.batch_payment_line:
    #         #     if payment_line.state == 'sent':
    #         #         logged_user = self._uid
    #         #         print(logged_user)
    #         #         get_logged_user_branch = self.env['res.users'].search([('id', '=', self._uid)]).branch_id
    #         #         print(get_logged_user_branch.id)
    #         #         _default_warehouse = self.env.user.context_default_warehouse_id.name
    #         #         approved_setting = self.env['customer.payment.approval'].search([])
    #         #         if approved_setting.approve_customer_payment:
    #         #             payment_line.state = 'waiting_for_approval'
    #         #             partner_ids = []
    #         #             display_message = 'An customer payment is posted on the "waiting for approval" state. Please approve it.'
    #         #             for approver in approved_setting.customer_payment_approver_ids:
    #         #                 get_approval_user_branch = self.env['res.users'].search([('id', '=', approver.id)]).branch_id
    #         #                 print(get_approval_user_branch.id)
    #         #                 # print('Salesman Default warehouse', salesman_default_warehouse)
    #         #                 # print('Approver Default warehouse', approver.context_default_warehouse_id.name)
    #         #                 if get_logged_user_branch.id == get_approval_user_branch.id:
    #         #                     # if approver.context_default_warehouse_id.name == _default_warehouse:
    #         #                     approver.notify_info(message=display_message)
    #         #                     partner_ids.append(
    #         #                         self.env['res.partner'].search([('name', 'ilike', approver.name)], limit=1).id)
    #         #
    #         #             # sale_order = self.env['sale.order'].browse(self.env.context.get('active_ids'))
    #         #             payment_line.message_post(body=display_message, subtype='mt_note', partner_ids=partner_ids)
    #         #         else:
    #         #             payment_line.state = 'sent'
    #
    # def btn_reset_to_draft(self):
    #     if self.temp_payment_id:
    #         payment_id_list = self.temp_payment_id.split(" , ")
    #         payment_id_list.remove('')
    #         payment_list = self.env['account.payment'].search([('id', 'in', payment_id_list)])
    #
    #         for payment_line in payment_list:
    #             if (payment_line.state == 'dishonored') or (payment_line.state == 'cancelled') or (payment_line.state == 'reconciled'):
    #                 moves = payment_line.mapped('move_line_ids.move_id')
    #                 moves.filtered(lambda move: move.state == 'posted').button_draft()
    #                 moves.with_context(force_delete=True).unlink()
    #                 payment_line.state == 'draft'
    #                 payment_line.invoice_ids == False
    #
    #     # for payment_line in self.batch_payment_line:
    #     #     if (payment_line.state == 'dishonored') or (payment_line.state == 'cancelled') or (payment_line.state == 'reconciled'):
    #     #         moves = payment_line.mapped('move_line_ids.move_id')
    #     #         moves.filtered(lambda move: move.state == 'posted').button_draft()
    #     #         moves.with_context(force_delete=True).unlink()
    #     #         payment_line.state == 'draft'
    #     #         payment_line.invoice_ids == False
    #
    # def btn_dishonor_all(self):
    #     if self.temp_payment_id:
    #         payment_id_list = self.temp_payment_id.split(" , ")
    #         payment_id_list.remove('')
    #         payment_list = self.env['account.payment'].search([('id', 'in', payment_id_list)])
    #
    #         for payment_line in payment_list:
    #             if payment_line.state == 'waiting_for_approval':
    #                 payment_line.dishonor_date = date.today()
    #                 payment_line.state = 'dishonored'
    #                 payment_line.dishonor_count = payment_line.dishonor_count + 1
    #                 get_partner = self.env['res.partner'].browse(payment_line.partner_id.id)
    #                 get_partner.update({
    #                     'active': False
    #                 })
    #
    #         # for payment_line in self.batch_payment_line:
    #         #     if (payment_line.state == 'sent'):
    #         #         payment_line.dishonor_date = date.today()
    #         #         payment_line.state = 'dishonored'
    #         #         payment_line.dishonor_count = payment_line.dishonor_count + 1
    #         #         get_partner = self.env['res.partner'].browse(self.partner_id.id)
    #         #         get_partner.update({
    #         #             'active': False
    #         #         })
    #             # it = item
    #             # print(item)
    #             # print("sdfsd")
    #         # for payment_line in self.batch_payment_line:
    #         #     print(payment_line)
    #         # print("Dishonor click")
    #
    # def btn_approve(self):
    #     """ Create the journal items for the payment and update the payment's state to 'posted'.
    #                 A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
    #                 and another in the destination reconcilable account (see _compute_destination_account_id).
    #                 If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
    #                 If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
    #             """
    #     if self.temp_payment_id:
    #         payment_id_list = self.temp_payment_id.split(" , ")
    #         payment_id_list.remove('')
    #         payment_list = self.env['account.payment'].search([('id', 'in', payment_id_list)])
    #
    #         for payment_line in payment_list:
    #             if payment_line.state == 'waiting_for_approval':
    #                 AccountMove = self.env['account.move'].with_context(default_type='entry')
    #                 for rec in payment_line:
    #                     payment_line.honor_date = date.today()
    #                     if rec.state != 'waiting_for_approval':
    #                         raise UserError(_("Only a waiting for approval payment can be posted."))
    #
    #                     if any(inv.state != 'posted' for inv in rec.invoice_ids):
    #                         raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))
    #
    #                     # keep the name in case of a payment reset to draft
    #                     if not rec.name:
    #                         # Use the right sequence to set the name
    #                         if rec.payment_type == 'transfer':
    #                             sequence_code = 'account.payment.transfer'
    #                         else:
    #                             if rec.partner_type == 'customer':
    #                                 if rec.payment_type == 'inbound':
    #                                     sequence_code = 'account.payment.customer.invoice'
    #                                 if rec.payment_type == 'outbound':
    #                                     sequence_code = 'account.payment.customer.refund'
    #                             if rec.partner_type == 'supplier':
    #                                 if rec.payment_type == 'inbound':
    #                                     sequence_code = 'account.payment.supplier.refund'
    #                                 if rec.payment_type == 'outbound':
    #                                     sequence_code = 'account.payment.supplier.invoice'
    #                         rec.name = self.env['ir.sequence'].next_by_code(sequence_code, sequence_date=rec.payment_date)
    #                         if not rec.name and rec.payment_type != 'transfer':
    #                             raise UserError(
    #                                 _("You have to define a sequence for %s in your company.") % (sequence_code,))
    #
    #                     moves = AccountMove.create(rec._prepare_payment_moves())
    #                     moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()
    #
    #                     # Update the state / move before performing any reconciliation.
    #                     move_name = payment_line._get_move_name_transfer_separator().join(moves.mapped('name'))
    #                     rec.write({'state': 'posted', 'move_name': move_name})
    #
    #                     if rec.payment_type in ('inbound', 'outbound'):
    #                         # ==== 'inbound' / 'outbound' ====
    #                         if rec.invoice_ids:
    #                             (moves[0] + rec.invoice_ids).line_ids \
    #                                 .filtered(
    #                                 lambda line: not line.reconciled and line.account_id == rec.destination_account_id) \
    #                                 .reconcile()
    #                     elif rec.payment_type == 'transfer':
    #                         # ==== 'transfer' ====
    #                         moves.mapped('line_ids') \
    #                             .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id) \
    #                             .reconcile()
    #
    #             flag_state = 'finished'
    #             for payment_line in payment_list:
    #                 if (payment_line.state != 'posted'):
    #                     flag_state = 'processing'
    #                     break
    #
    #             self.state = flag_state
    #             return True
    #
    #     # for payment_line in self.batch_payment_line:
    #     #     if (payment_line.state == 'waiting_for_approval'):
    #     #         AccountMove = self.env['account.move'].with_context(default_type='entry')
    #     #         for rec in payment_line:
    #     #             payment_line.honor_date = date.today()
    #     #             if rec.state != 'waiting_for_approval':
    #     #                 raise UserError(_("Only a waiting for approval payment can be posted."))
    #     #
    #     #             if any(inv.state != 'posted' for inv in rec.invoice_ids):
    #     #                 raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))
    #     #
    #     #             # keep the name in case of a payment reset to draft
    #     #             if not rec.name:
    #     #                 # Use the right sequence to set the name
    #     #                 if rec.payment_type == 'transfer':
    #     #                     sequence_code = 'account.payment.transfer'
    #     #                 else:
    #     #                     if rec.partner_type == 'customer':
    #     #                         if rec.payment_type == 'inbound':
    #     #                             sequence_code = 'account.payment.customer.invoice'
    #     #                         if rec.payment_type == 'outbound':
    #     #                             sequence_code = 'account.payment.customer.refund'
    #     #                     if rec.partner_type == 'supplier':
    #     #                         if rec.payment_type == 'inbound':
    #     #                             sequence_code = 'account.payment.supplier.refund'
    #     #                         if rec.payment_type == 'outbound':
    #     #                             sequence_code = 'account.payment.supplier.invoice'
    #     #                 rec.name = self.env['ir.sequence'].next_by_code(sequence_code, sequence_date=rec.payment_date)
    #     #                 if not rec.name and rec.payment_type != 'transfer':
    #     #                     raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))
    #     #
    #     #             moves = AccountMove.create(rec._prepare_payment_moves())
    #     #             moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()
    #     #
    #     #             # Update the state / move before performing any reconciliation.
    #     #             move_name = payment_line._get_move_name_transfer_separator().join(moves.mapped('name'))
    #     #             rec.write({'state': 'posted', 'move_name': move_name})
    #     #
    #     #             if rec.payment_type in ('inbound', 'outbound'):
    #     #                 # ==== 'inbound' / 'outbound' ====
    #     #                 if rec.invoice_ids:
    #     #                     (moves[0] + rec.invoice_ids).line_ids \
    #     #                         .filtered(lambda line: not line.reconciled and line.account_id == rec.destination_account_id) \
    #     #                         .reconcile()
    #     #             elif rec.payment_type == 'transfer':
    #     #                 # ==== 'transfer' ====
    #     #                 moves.mapped('line_ids') \
    #     #                     .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id) \
    #     #                     .reconcile()
    #     #
    #     # flag_state = 'finished'
    #     # for payment_line in self.batch_payment_line:
    #     #     if (payment_line.state != 'posted'):
    #     #         flag_state = 'processing'
    #     #         break
    #     #
    #     # self.state = flag_state
    #     # return True
    #     # print("Dishonor click")

    @api.onchange('date_start', 'cheque_no', 'cheque_type', 'branch_id', 'date_end')
    def _on_change_date_start(self):
        self.page_change_event()

    def page_change_event(self):
        doamin = [('effective_date', '>=', self.date_start), ('effective_date', '<=', self.date_end), ('payment_type', '=', 'inbound')]
        # data_list = self.env['account.payment'].search([('effective_date', '=', self.date_start)])
        if self.cheque_no:
            doamin.append(('cheque_reference', 'like', self.cheque_no))
        if self.cheque_type:
            doamin.append(('partner_type', '=', self.cheque_type))
        if self.branch_id:
            doamin.append(('branch_id', 'in', self.branch_id.ids))

        draft_domain = copy.deepcopy(doamin)
        draft_domain.append(('state', '=', 'draft'))
        draft_list = formating_list(self.env['account.payment'].search(draft_domain))
        self.draft_payment_line_ids = draft_list

        sent_domain = copy.deepcopy(doamin)
        sent_domain.append(('state', '=', 'waiting_for_approval'))
        sent_list = formating_list(self.env['account.payment'].search(sent_domain))
        self.sent_payment_line_ids = sent_list

        # waiting_for_approval_domain = copy.deepcopy(doamin)
        # waiting_for_approval_domain.append(('state', '=', 'waiting_for_approval'))
        # waiting_for_approval_list = formating_list(self.env['account.payment'].search(waiting_for_approval_domain))
        # self.submit_for_approval_payment_line_ids = waiting_for_approval_list

        posted_domain = copy.deepcopy(doamin)
        posted_domain.append(('state', '=', 'posted'))
        posted_list = formating_list(self.env['account.payment'].search(posted_domain))
        self.approve_payment_line_ids = posted_list

        dishonored_domain = copy.deepcopy(doamin)
        dishonored_domain.append(('state', '=', 'dishonored'))
        dishonored_domain.append(('not_respone_by_effective_date', '!=', True))
        dishonored_list = formating_list(self.env['account.payment'].search(dishonored_domain))
        self.dishonored_payment_line_ids = dishonored_list

        dishonored_by_not_response_domain = copy.deepcopy(doamin)
        dishonored_by_not_response_domain.append(('state', '=', 'dishonored'))
        dishonored_by_not_response_domain.append(('not_respone_by_effective_date', '=', True))
        dishonored_by_not_response_list = formating_list(self.env['account.payment'].search(dishonored_by_not_response_domain))
        self.dishonor_by_not_responding_line_ids = dishonored_by_not_response_list

        # draft_list = formating_list(self.env['account.payment'].search(doamin))
        # draft_list = formating_list(self.env['account.payment'].search(doamin))
        # draft_list = formating_list(self.env['account.payment'].search(doamin))
        # draft_list = formating_list(self.env['account.payment'].search(doamin))
        # draft_list = formating_list(self.env['account.payment'].search(doamin))

        # self.draft_payment_line_ids = list
        # self.sent_payment_line_ids = list
        # self.submit_for_approval_payment_line_ids = list
        # self.dishonored_payment_line_ids = list
        # self.approve_payment_line_ids = list
        # print(list)

