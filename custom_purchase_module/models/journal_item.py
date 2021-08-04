from dateutil.utils import today

from odoo import api, fields, models, _
from odoo.tools import float_compare
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang

from datetime import date, timedelta
from itertools import groupby
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import json
import re

class journalItemCalculate(models.Model):
    _inherit = 'account.move'

    @api.model
    def _move_autocomplete_invoice_lines_create(self, vals_list):
        ''' During the create of an account.move with only 'invoice_line_ids' set and not 'line_ids', this method is called
        to auto compute accounting lines of the invoice. In that case, accounts will be retrieved and taxes, cash rounding
        and payment terms will be computed. At the end, the values will contains all accounting lines in 'line_ids'
        and the moves should be balanced.

        :param vals_list:   The list of values passed to the 'create' method.
        :return:            Modified list of values.
        '''
        new_vals_list = []
        for vals in vals_list:
            # new_vals_list.append(vals)
            # print(vals.get('invoice_line_ids')[0][2]['product_id'])
            if vals.get('invoice_line_ids') != None:
                for line in vals.get('line_ids'):
                    for inv_line in vals.get('invoice_line_ids'):
                        print(line)
                        print(line[2]['product_id'])
                        if inv_line[2]['product_id'] == line[2]['product_id']:
                            line[2]['po_price'] = inv_line[2]['po_price']



                if not vals.get('invoice_line_ids'):
                    new_vals_list.append(vals)
                    continue
                if vals.get('line_ids'):
                    vals.pop('invoice_line_ids', None)
                    new_vals_list.append(vals)
                    continue
                if not vals.get('type') and not self._context.get('default_type'):
                    vals.pop('invoice_line_ids', None)
                    new_vals_list.append(vals)
                    continue
                vals['type'] = vals.get('type', self._context.get('default_type', 'entry'))
                if not vals['type'] in self.get_invoice_types(include_receipts=True):
                    new_vals_list.append(vals)
                    continue

                vals['line_ids'] = vals.pop('invoice_line_ids')

                if vals.get('invoice_date') and not vals.get('date'):
                    vals['date'] = vals['invoice_date']

                ctx_vals = {'default_type': vals.get('type') or self._context.get('default_type')}
                if vals.get('journal_id'):
                    ctx_vals['default_journal_id'] = vals['journal_id']
                    # reorder the companies in the context so that the company of the journal
                    # (which will be the company of the move) is the main one, ensuring all
                    # property fields are read with the correct company
                    journal_company = self.env['account.journal'].browse(vals['journal_id']).company_id
                    allowed_companies = self._context.get('allowed_company_ids', journal_company.ids)
                    reordered_companies = sorted(allowed_companies, key=lambda cid: cid != journal_company.id)
                    ctx_vals['allowed_company_ids'] = reordered_companies
                self_ctx = self.with_context(**ctx_vals)
                new_vals = self_ctx._add_missing_default_values(vals)

                move = self_ctx.new(new_vals)
                new_vals_list.append(move._move_autocomplete_invoice_lines_values())

        return new_vals_list

    def _move_autocomplete_invoice_lines_write(self, vals):
        ''' During the write of an account.move with only 'invoice_line_ids' set and not 'line_ids', this method is called
        to auto compute accounting lines of the invoice. In that case, accounts will be retrieved and taxes, cash rounding
        and payment terms will be computed. At the end, the values will contains all accounting lines in 'line_ids'
        and the moves should be balanced.

        :param vals_list:   A python dict representing the values to write.
        :return:            True if the auto-completion did something, False otherwise.
        '''
        enable_autocomplete = 'invoice_line_ids' in vals  and True or False

        if not enable_autocomplete:
            return False

        vals['line_ids'] = vals.pop('invoice_line_ids')
        for invoice in self:
            invoice_new = invoice.with_context(default_type=invoice.type, default_journal_id=invoice.journal_id.id).new(origin=invoice)
            invoice_new.update(vals)
            values = invoice_new._move_autocomplete_invoice_lines_values()
            values.pop('invoice_line_ids', None)
            invoice.write(values)
        return True
    # def _move_autocomplete_invoice_lines_values(self):
    #     self.ensure_one()
    #
    #     line_currency = self.currency_id if self.currency_id != self.company_id.currency_id else False
    #     for line in self.line_ids:
    #         # Do something only on invoice lines.
    #         if line.exclude_from_invoice_tab:
    #             continue
    #
    #         # Shortcut to load the demo data.
    #         # Doing line.account_id triggers a default_get(['account_id']) that could returns a result.
    #         # A section / note must not have an account_id set.
    #         if not line._cache.get('account_id') and not line.display_type and not line._origin:
    #             line.account_id = line._get_computed_account()
    #             if not line.account_id:
    #                 if self.is_sale_document(include_receipts=True):
    #                     line.account_id = self.journal_id.default_credit_account_id
    #                 elif self.is_purchase_document(include_receipts=True):
    #                     line.account_id = self.journal_id.default_debit_account_id
    #         if line.product_id and not line._cache.get('name'):
    #             line.name = line._get_computed_name()
    #
    #         # Compute the account before the partner_id
    #         # In case account_followup is installed
    #         # Setting the partner will get the account_id in cache
    #         # If the account_id is not in cache, it will trigger the default value
    #         # Which is wrong in some case
    #         # It's better to set the account_id before the partner_id
    #         # Ensure related fields are well copied.
    #         line.partner_id = self.partner_id
    #         line.date = self.date
    #         line.recompute_tax_line = True
    #         line.currency_id = line_currency
    #
    #     self.line_ids._onchange_price_subtotal()
    #     self._recompute_dynamic_lines(recompute_all_taxes=True)
    #
    #     values = self._convert_to_write(self._cache)
    #     # values.pop('invoice_line_ids', None)
    #     return values

    # def _move_autocomplete_invoice_lines_write(self, vals):
    #     enable_autocomplete = 'invoice_line_ids' in vals and 'line_ids' not in vals and True or False
    #
    #     if not enable_autocomplete:
    #         return False
    #
    #     # vals['line_ids'] = vals.pop('invoice_line_ids')
    #     for invoice in self:
    #         invoice_new = invoice.with_context(default_type=invoice.type, default_journal_id=invoice.journal_id.id).new(
    #             origin=invoice)
    #         invoice_new.update(vals)
    #         values = invoice_new._move_autocomplete_invoice_lines_values()
    #         # values.pop('invoice_line_ids', None)
    #         invoice.write(values)
    #     return True
    #    # self.action_journal_cal()

    def action_journal_cal(self):
        line_ids=[]
        #calculate account_payable for two field
        #account_payable 2
        #account_name
        #Branch
        #Label
        #Debit
        #Credit
        #Tax Grid
        # self.line_ids.unlink()
        account_payable_id=self.env['account.move.line'].search([('move_id','=',self.id),('account_internal_type','=','payable')]).account_root_id


        acc_payable=self.env['account.account'].search([('company_id','=',self.env.user.company_id.id),('root_id','=',account_payable_id.id)])
        currency=self.env['res.currency'].search([('id','=',self.currency_id.id)])
        default_currency=self.invoice_line_ids.company_currency_id
        default_currency_rate=self.env['res.currency.rate'].search([('currency_id','=',self.invoice_line_ids.company_currency_id.id),('company_id','=',self.env.user.company_id.id)])
        if len(self.invoice_line_ids.ids)==1:
            query = """select sum(total_po),sum(price_subtotal) from account_move_line where id = {}""".format(
                self.invoice_line_ids.ids[0])
        else:
            query="""select sum(total_po),sum(price_subtotal) from account_move_line where id in {}""".format(tuple(self.invoice_line_ids.ids))
        self._cr.execute(query=query)
        total_po_unit_price=self._cr.fetchall()
        if currency.name=='BDT':
            po_price=total_po_unit_price[0][0]
            unit_price=total_po_unit_price[0][1]
        else:
            po_price=total_po_unit_price[0][0]/((default_currency.rounding/default_currency.local_currency)*100)
            unit_price=total_po_unit_price[0][1]/((default_currency.rounding/default_currency_rate.rate)*100)

        vals_po_price=(0,0,{
            'account_id':acc_payable.id,
            'branch_id':self.branch_id.id,
            'name':"",
            'debit':0,
            'credit':po_price+unit_price,
            'tag_ids':[]
        })
        # vals_unit_price=(0,0,{
        #     'account_id':197,
        #     'branch_id':self.branch_id.id,
        #     'name':"",
        #     'debit':0.0,
        #     'credit':unit_price,
        #     'tag_ids':[]
        # })
        line_ids.append(vals_po_price)
        # line_ids.append(vals_unit_price)
        query="""select aml.account_id,aml.product_id,aml.name,rcc.id,rcc.name,rc.id,rc.name,aml.price_subtotal,aml.total_po,aml.quantity,aml.price_unit,aml.po_price from account_move am
                left join account_move_line aml on aml.move_id=am.id
                left join res_currency rc on rc.id=am.currency_id
                left join res_currency rcc on rcc.id=aml.company_currency_id where am.id={} and aml.account_internal_type='other'""".format(self.id)
        self._cr.execute(query=query)
        product_journal=self._cr.fetchall()
        for product in product_journal:
            if product[1]:
                if product[6]=='BDT':
                    vals_po_price=(0,0,{
                        'product_id': product[1],
                        'account_id': product[0],
                        'branch_id': self.branch_id.id,
                        'name': product[2],
                        'debit': product[8]+product[7],
                        'credit': 0.0,
                        'tag_ids': [],
                        'quantity':product[9],
                        # 'price_unit':product[10],
                        'po_price':product[11]
                    })
                    line_ids.append(vals_po_price)
                    # vals_unit_price = (0, 0, {
                    #     'product_id': product[1],
                    #     'account_id': 185,
                    #     'branch_id': self.branch_id.id,
                    #     'name': product[2],
                    #     'debit': product[7],
                    #     'credit': 0.0,
                    #     'tag_ids': [],
                    #     'quantity': product[9],
                    #     # 'price_unit': product[10],
                    #     'po_price': product[11]
                    # })
                    # line_ids.append(vals_unit_price)
                else:
                    default_currency = self.env['res.currency'].search([('id','=',product[3])])
                    default_currency_rate = self.env['res.currency.rate'].search(
                        [('currency_id', '=', product[3]),
                         ('company_id', '=', self.env.user.company_id.id)])
                    po_price = product[8]/((default_currency.rounding/default_currency.local_currency) * 100)
                    unit_price = total_po_unit_price[0][1]/((default_currency.rounding/default_currency_rate.rate) * 100)
                    vals_po_price = (0, 0, {
                        'product_id':product[1],
                        'account_id': product[0],
                        'branch_id': self.branch_id.id,
                        'name': product[2],
                        'debit': po_price+unit_price,
                        'credit': 0.0,
                        'tag_ids': [],
                        'quantity': product[9],
                        # 'price_unit': product[10],
                        'po_price': product[11]

                    })
                    line_ids.append(vals_po_price)
                    # vals_unit_price = (0, 0, {
                    #     'product_id': product[1],
                    #     # 'account_id': product[0],
                    #     'account_id': 185,
                    #     'branch_id': self.branch_id.id,
                    #     'name': product[2],
                    #     'debit': unit_price,
                    #     'credit': 0.0,
                    #     'tag_ids': [],
                    #     'quantity': product[9],
                    #     # 'price_unit': product[10],
                    #     'po_price': product[11]
                    # })
                    # line_ids.append(vals_unit_price)
        self.line_ids.unlink()
        self.update({
            'line_ids':line_ids
        })
        # query="""SELECT product_id,name,is_landed_costs_line,account_id,quantity,po_price,price_unit,price_subtotal1 FROM account_move_line
        #         WHERE id IN(SELECT Max(id) FROM account_move_line)and move_id={}""".format(self.id)
        # self._cr.execute(query=query)
        # invoice_lines=self._cr.fetchall()
        # invoice_line_ids=[]
        # for inv_item in invoice_lines:
        #     vals = (0, 0, {
        #         'product_id': inv_item[0],
        #         'name': inv_item[1],
        #         'is_landed_costs_line':inv_item[2],
        #         'account_id': inv_item[3],
        #         'quantity': inv_item[4],
        #         'po_price': inv_item[5],
        #         'price_unit': inv_item[6],
        #         'price_subtotal1': inv_item[7],
        #
        #     })
        #     invoice_line_ids.append(vals)
        # self.invoice_line_ids.unlink()
        # self.update({
        #     'invoice_line_ids':invoice_line_ids
        # })


    def _recompute_payment_terms_lines(self):
        ''' Compute the dynamic payment term lines of the journal entry.'''
        self.ensure_one()
        in_draft_mode = self != self._origin
        today = fields.Date.context_today(self)
        self = self.with_context(force_company=self.journal_id.company_id.id)

        def _get_payment_terms_computation_date(self):
            ''' Get the date from invoice that will be used to compute the payment terms.
            :param self:    The current account.move record.
            :return:        A datetime.date object.
            '''
            if self.invoice_payment_term_id:
                return self.invoice_date or today
            else:
                return self.invoice_date_due or self.invoice_date or today

        def _get_payment_terms_account(self, payment_terms_lines):
            ''' Get the account from invoice that will be set as receivable / payable account.
            :param self:                    The current account.move record.
            :param payment_terms_lines:     The current payment terms lines.
            :return:                        An account.account record.
            '''
            if payment_terms_lines:
                # Retrieve account from previous payment terms lines in order to allow the user to set a custom one.
                return payment_terms_lines[0].account_id
            elif self.partner_id:
                # Retrieve account from partner.
                if self.is_sale_document(include_receipts=True):
                    return self.partner_id.property_account_receivable_id
                else:
                    return self.partner_id.property_account_payable_id
            else:
                # Search new account.
                domain = [
                    ('company_id', '=', self.company_id.id),
                    ('internal_type', '=', 'receivable' if self.type in ('out_invoice', 'out_refund', 'out_receipt') else 'payable'),
                ]
                return self.env['account.account'].search(domain, limit=1)

        def _compute_payment_terms(self, date, total_balance, total_amount_currency):
            ''' Compute the payment terms.
            :param self:                    The current account.move record.
            :param date:                    The date computed by '_get_payment_terms_computation_date'.
            :param total_balance:           The invoice's total in company's currency.
            :param total_amount_currency:   The invoice's total in invoice's currency.
            :return:                        A list <to_pay_company_currency, to_pay_invoice_currency, due_date>.
            '''
            if self.invoice_payment_term_id:
                to_compute = self.invoice_payment_term_id.compute(total_balance, date_ref=date, currency=self.currency_id)
                if self.currency_id != self.company_id.currency_id:
                    # Multi-currencies.
                    to_compute_currency = self.invoice_payment_term_id.compute(total_amount_currency, date_ref=date, currency=self.currency_id)
                    return [(b[0], b[1], ac[1]) for b, ac in zip(to_compute, to_compute_currency)]
                else:
                    # Single-currency.
                    return [(b[0], b[1], 0.0) for b in to_compute]
            else:
                return [(fields.Date.to_string(date), total_balance, total_amount_currency)]

        def _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute):
            ''' Process the result of the '_compute_payment_terms' method and creates/updates corresponding invoice lines.
            :param self:                    The current account.move record.
            :param existing_terms_lines:    The current payment terms lines.
            :param account:                 The account.account record returned by '_get_payment_terms_account'.
            :param to_compute:              The list returned by '_compute_payment_terms'.
            '''
            # As we try to update existing lines, sort them by due date.
            existing_terms_lines = existing_terms_lines.sorted(lambda line: line.date_maturity or today)
            existing_terms_lines_index = 0

            # Recompute amls: update existing line or create new one for each payment term.
            new_terms_lines = self.env['account.move.line']
            for date_maturity, balance, amount_currency in to_compute:
                if self.journal_id.company_id.currency_id.is_zero(balance) and len(to_compute) > 1:
                    continue

                if existing_terms_lines_index < len(existing_terms_lines):
                    # Update existing line.
                    candidate = existing_terms_lines[existing_terms_lines_index]
                    existing_terms_lines_index += 1
                    candidate.update({
                        'date_maturity': date_maturity,
                        'amount_currency': -amount_currency,
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                    })
                else:
                    # Create new line.
                    create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
                    candidate = create_method({
                        'name': self.invoice_payment_ref or '',
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                        'quantity': 1.0,
                        'amount_currency': -amount_currency,
                        'date_maturity': date_maturity,
                        'move_id': self.id,
                        'currency_id': self.currency_id.id if self.currency_id != self.company_id.currency_id else False,
                        'account_id': account.id,
                        'partner_id': self.commercial_partner_id.id,
                        'exclude_from_invoice_tab': True,
                    })
                new_terms_lines += candidate
                if in_draft_mode:
                    candidate._onchange_amount_currency()
                    candidate._onchange_balance()
            return new_terms_lines

        existing_terms_lines = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
        others_lines = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
        total_po=0.0
        for o in others_lines:
            print(o)
            o['debit']=o['price_subtotal1']

            total_po+=o['total_po']
            print(o)
        company_currency_id = self.company_id.currency_id

        total_balance = sum(others_lines.mapped(lambda l: company_currency_id.round(l.balance)))
        total_amount_currency = sum(others_lines.mapped('amount_currency'))

        if not others_lines:
            self.line_ids -= existing_terms_lines
            return

        computation_date = _get_payment_terms_computation_date(self)
        account = _get_payment_terms_account(self, existing_terms_lines)
        to_compute = _compute_payment_terms(self, computation_date, total_balance, total_amount_currency)
        new_terms_lines = _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute)

        # Remove old terms lines that are no longer needed.
        self.line_ids -= existing_terms_lines - new_terms_lines

        if new_terms_lines:
            self.invoice_payment_ref = new_terms_lines[-1].name or ''
            self.invoice_date_due = new_terms_lines[-1].date_maturity






