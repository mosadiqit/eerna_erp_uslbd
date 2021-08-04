# -*- coding: utf-8 -*-
import base64
from datetime import datetime
from io import BytesIO

import xlsxwriter
from num2words import num2words

from odoo import fields, models, _
# from odoo.addons.account_check_printing.models.res_company import res_company
from odoo.exceptions import UserError
from custom_module.accounting_report.models.usl_xlxs_report_tools import UslXlxsReportUtil as utill
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, get_lang


class AccountPartnerLedger(models.TransientModel):
    _name = "account.report.partner.ledger"
    _inherit = 'account.common.partner.report'
    _description = "Account Partner Ledger"

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)

    date_from = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_to = fields.Date(string='End Date', required=True, default=fields.Date.today)

    amount_currency = fields.Boolean("With Currency",
                                     help="It adds the currency column on report if the currency differs from the company currency.")
    reconciled = fields.Boolean(string='Reconciled Entries', help='Show reconcile entries', default=True)

    initial_balance = fields.Boolean(string='Include Initial Balances',
                                     help='If you selected date, this field allow you to add a row to display the amount of debit/credit/balance that precedes the filter you\'ve set.',
                                     default=True)

    def _lines(self, data, partner):  # duke
        print('2')
        # print("data",data)
        # print("partner",partner)
        full_account = []
        company_id = data['form']['company_id'][0]
        currency = self.env['res.currency']
        print('company id', company_id)

        # Initial Balance Calculation
        sum = 0.0
        init_balance = data['form'].get('initial_balance', True)
        print('init balance is',init_balance)
        if init_balance:
            init_query_get_data = self.env['account.move.line'].with_context(
                date_from=data['form'].get('date_from'), date_to=False, initial_bal=True,
                strict_range=True)._query_get()
            _init_params = [company_id, partner.id, tuple(data['computed']['move_state']),
                            tuple(data['computed']['account_ids'])] + \
                           init_query_get_data[2]

            query = """
                         SELECT '' as id, '' as date, '' as code, '' as a_code, '' as a_name, 'Opening Balance' as ref, '' as move_name, '' as name,COALESCE(SUM("account_move_line".debit),0.0) as debit,COALESCE(SUM("account_move_line".credit),0.0) as credit, '' as amount_currency, '' as currency_id, '' AS currency_code, '' as remarks
                                    FROM account_move_line
                                    LEFT JOIN account_journal j ON ("account_move_line".journal_id = j.id)
                                    LEFT JOIN account_account acc ON ("account_move_line".account_id = acc.id)
                                    LEFT JOIN res_currency c ON ("account_move_line".currency_id=c.id)
                                    LEFT JOIN account_move m ON (m.id="account_move_line".move_id)
                                    LEFT JOIN sale_order so on (so.name=m.invoice_origin and so.company_id = m.company_id and m.type = 'out_invoice')
                                    WHERE m.company_id=%s AND "account_move_line".partner_id = %s
                                        AND m.state IN %s
                                        AND "account_move_line".account_id IN %s AND """ + init_query_get_data[1] + """
                                        """

            self.env.cr.execute(query, tuple(_init_params))
            _int_res = self.env.cr.dictfetchall()

            lang_code = self.env.context.get('lang') or 'en_US'
            lang = self.env['res.lang']
            lang_id = lang._lang_get(lang_code)
            date_format = lang_id.date_format
            for r in _int_res:
                # r['date'] = datetime.strptime(str(r['date']), DEFAULT_SERVER_DATE_FORMAT).strftime(date_format)
                r['displayed_name'] = '-'.join(
                    r[field_name] for field_name in ('move_name', 'ref', 'name')
                    if r[field_name] not in (None, '', '/')
                )
                sum += r['debit'] - r['credit']
                r['progress'] = sum
                r['currency_id'] = currency.browse(r.get('currency_id'))
                full_account.append(r)

        query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".reconciled = false '
        params = [company_id, partner.id, tuple(data['computed']['move_state']),
                  tuple(data['computed']['account_ids'])] + query_get_data[2]
        query = """
                SELECT "account_move_line".id, "account_move_line".date, j.code, acc.code as a_code, acc.name as a_name, "account_move_line".ref,"account_move_line".move_id, 
                CASE WHEN m.state = 'draft' THEN 'Draft' ELSE m.name END as move_name, 
                "account_move_line".name, "account_move_line".debit, "account_move_line".credit, "account_move_line".amount_currency,"account_move_line".currency_id, c.symbol AS currency_code, so.note as remarks
                FROM """ + query_get_data[0] + """
                LEFT JOIN account_journal j ON ("account_move_line".journal_id = j.id)
                LEFT JOIN account_account acc ON ("account_move_line".account_id = acc.id)
                LEFT JOIN res_currency c ON ("account_move_line".currency_id=c.id)
                LEFT JOIN account_move m ON (m.id="account_move_line".move_id)
    			LEFT JOIN sale_order so on (so.name=m.invoice_origin and so.company_id = m.company_id and m.type = 'out_invoice')
                WHERE m.company_id=%s AND "account_move_line".partner_id = %s
                    AND m.state IN %s
                    AND "account_move_line".account_id IN %s AND """ + query_get_data[1] + reconcile_clause + """
                    ORDER BY "account_move_line".date"""
        print(query)
        self.env.cr.execute(query, tuple(params))
        res = self.env.cr.dictfetchall()
        # sum = 0.0
        lang_code = self.env.context.get('lang') or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)
        date_format = lang_id.date_format
        for r in res:
            r['date'] = datetime.strptime(str(r['date']), DEFAULT_SERVER_DATE_FORMAT).strftime(date_format)
            r['displayed_name'] = '-'.join(
                r[field_name] for field_name in ('move_name', 'ref', 'name')
                if r[field_name] not in (None, '', '/')
            )
            sum += r['debit'] - r['credit']
            r['progress'] = sum
            r['currency_id'] = currency.browse(r.get('currency_id'))
            move_id = r['move_id']
            r['move_id'] = move_id
            full_account.append(r)
        print("full_account", full_account)
        return full_account

    def _sum_partner(self, data, partner, field):  # duke
        print('3')
        company_id = data['form']['company_id'][0]
        if field not in ['debit', 'credit', 'debit - credit']:
            return
        result = 0.0

        # query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()

        query_get_data = self.env['account.move.line'].with_context(
            date_from=False, date_to=False, initial_bal=False, strict_range=True)._query_get()

        # reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".reconciled = false '

        reconcile_clause = ' "account_move_line".reconciled = true '

        params = [company_id, partner.id, tuple(data['computed']['move_state']),
                  tuple(data['computed']['account_ids'])] + query_get_data[2]

        # query = """SELECT sum(""" + field + """)
        #         FROM """ + query_get_data[0] + """, account_move AS m
        #         WHERE "account_move_line".partner_id = %s
        #             AND m.id = "account_move_line".move_id
        #             AND m.state IN %s
        #             AND account_id IN %s
        #             AND """ + query_get_data[1] + reconcile_clause

        query = """SELECT sum(""" + field + """)
                            FROM account_move_line, account_move AS m
                            WHERE m.company_id=%s AND "account_move_line".partner_id = %s
                                AND m.id = "account_move_line".move_id
                                AND m.state IN %s
                                AND account_id IN %s
                                """

        self.env.cr.execute(query, tuple(params))

        contemp = self.env.cr.fetchone()
        print("contemp", contemp)
        if contemp is not None:
            result = contemp[0] or 0.0
        return result

    def _print_report(self, data): # this method overrided in account_partner_ledger_filter
        print("b", data)
        data = self.pre_print_report(data)
        data['form'].update({'reconciled': self.reconciled, 'amount_currency': self.amount_currency,
                             'initial_balance': self.initial_balance})
        print('yes ekhane dukse')
        if data['form'].get('initial_balance') and not data['form'].get('date_from'):
            raise UserError(_("You must define a Start Date"))

        return self.env.ref('gts_financial_pdf_report.action_report_partnerledger').report_action(self, data=data)

    def excel_report(self):
        self.ensure_one()
        data = {}
        print('ibrahim ibrahim al azhar')
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'company_id'])[0]
        used_context = self._build_contexts(data)
        print('used_context')
        data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
        print('The ultimate data is', data)
        data = self.pre_print_report(data)
        data['form'].update({'reconciled': self.reconciled, 'amount_currency': self.amount_currency,
                             'initial_balance': self.initial_balance})
        print('yes ekhane dukse')
        # if data['form'].get('initial_balance') and not data['form'].get('date_from'):
        #     raise UserError(_("You must define a Start Date")
        # return self.with_context(discard_logo_check=True)._print_report(data)

        print('_get_report_values on report.gts_financial_pdf_report.report_partnerledger')
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        data['computed'] = {}

        data = self.pre_print_report(data)
        data['form'].update({'reconciled': self.reconciled, 'amount_currency': self.amount_currency,
                             'partner_ids': self.partner_ids.ids, 'mis_summery': self.mis_summery})
        # return self.env.ref('gts_financial_pdf_report.action_report_partnerledger').report_action(self, data=data)

        obj_partner = self.env['res.partner']
        query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        print('query_get_data', data['form'].get('used_context', {}))
        data['computed']['move_state'] = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            data['computed']['move_state'] = ['posted']
        if data['form'].get('target_move') == 'all':
            print(query_get_data[1])
            new_string = query_get_data[1].replace("date", "collection_date")
            query_get_data = list(query_get_data)
            query_get_data.pop(1)
            query_get_data.insert(1, new_string)
            query_get_data = tuple(query_get_data)
        result_selection = data['form'].get('result_selection', 'customer')
        if result_selection == 'supplier':
            data['computed']['ACCOUNT_TYPE'] = ['payable']
        elif result_selection == 'customer':
            data['computed']['ACCOUNT_TYPE'] = ['receivable']
        else:
            data['computed']['ACCOUNT_TYPE'] = ['payable', 'receivable']

        self.env.cr.execute("""
                    SELECT a.id
                    FROM account_account a
                    WHERE a.internal_type IN %s
                    AND NOT a.deprecated""", (tuple(data['computed']['ACCOUNT_TYPE']),))
        data['computed']['account_ids'] = [a for (a,) in self.env.cr.fetchall()]
        params = [tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + query_get_data[2]
        reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '
        query = """
                    SELECT DISTINCT "account_move_line".partner_id
                    FROM """ + query_get_data[0] + """, account_account AS account, account_move AS am
                    WHERE "account_move_line".partner_id IS NOT NULL
                        AND "account_move_line".account_id = account.id
                        AND am.id = "account_move_line".move_id
                        AND am.state IN %s
                        AND "account_move_line".account_id IN %s
                        AND NOT account.deprecated
                        AND """ + query_get_data[1] + reconcile_clause
        print(query)
        self.env.cr.execute(query, tuple(params))
        # ---------------------Taking only selected partners---------------------------
        if data['form']['partner_ids']:
            partner_ids = data['form']['partner_ids']
        else:
            partner_ids = [res['partner_id'] for res in self.env.cr.dictfetchall()]
        # -----------------------------------------------------------------------------
        # partner_ids = [res['partner_id'] for res in self.env.cr.dictfetchall()]
        where_partner_ids = "1=1"
        where_pay_partner_ids = "1=1"
        partners = obj_partner.browse(partner_ids)
        partners = sorted(partners, key=lambda x: (x.ref or '', x.name or ''))
        print('partners', partners)

        is_mis_summery = data['form'].get('mis_summery')
        branch_ids = data['form'].get('branch_ids')
        company_id = data['form'].get('company_id')[0]
        target_move = data['form'].get('target_move')
        branch_id = branch_ids['branch_ids']
        security_money = 0
        if is_mis_summery:

            if partner_ids:
                where_partner_ids = " id in %s" % str(tuple(partner_ids)).replace(',)', ')')
                where_pay_partner_ids = "rp.id in %s" % str(tuple(partner_ids)).replace(',)', ')')
            # Credit Limit
            # query1 = """select COALESCE(res_partner.credit_limit) from res_partner where {}""".format(where_partner_ids)
            # self._cr.execute(query=query1)
            # result_credit = self._cr.fetchall()
            # crLimit = result_credit[0][0]
            crLimit = 0
            # security_money = 0
            partner_info = self.env['res.partner'].browse(partner_ids)
            if partner_info:
                crLimit = partner_info.credit_limit
                security_money = partner_info.security_money
            # print('credit limit - ',result_credit)

            # Current Month Sales
            if target_move == 'posted':
                query2 = """select COALESCE(sum(credit),0) from account_move_line where partner_id = {} and account_root_id=52048 and date between (select cast(date_trunc('month', current_date) as date)) and (cast(date_trunc('month',
                                current_date)+INTERVAL '1 MONTH - 1 day' as date)) and parent_state = 'posted' and company_id = {}""".format(
                    partner_ids[0], company_id)
            else:
                query2 = """select COALESCE(sum(credit),0) from account_move_line where partner_id = {} and account_root_id=52048 and date between (select cast(date_trunc('month', current_date) as date)) and (cast(date_trunc('month',
                                    current_date)+INTERVAL '1 MONTH - 1 day' as date)) and company_id = {}""".format(
                    partner_ids[0], company_id)

            self._cr.execute(query=query2)
            cm_sales = self._cr.fetchall()
            current_month_sales = cm_sales[0][0]
            # current_month_sales = 0
            # val = self.env['account.move.line'].search([('partner_id', '=', partner_ids)]).sum('credit')
            # val = self.env['account.move.line'].search([('partner_id', '=', partner_ids)]).credit
            # current_month_sale = sum(self.env['account.move.line'].search([('partner_id', '=', partner_ids)]).credit)

            # Last Month Sales
            if target_move == 'posted':
                query3 = """select COALESCE(sum(credit),0) from account_move_line where partner_id = {} and account_root_id=52048 and date between (select cast(date_trunc('month', current_date)-INTERVAL '1 MONTH' as date)) and (select cast(date_trunc('month',
                                current_date)-INTERVAL '1 MONTH'+INTERVAL '1 MONTH - 1 day' as date)) and parent_state = 'posted' and company_id = {}""".format(
                    partner_ids[0], company_id)
            else:
                query3 = """select COALESCE(sum(credit),0) from account_move_line where partner_id = {} and account_root_id=52048 and date between (select cast(date_trunc('month', current_date)-INTERVAL '1 MONTH' as date)) and (select cast(date_trunc('month',
                                current_date)-INTERVAL '1 MONTH'+INTERVAL '1 MONTH - 1 day' as date)) and company_id = {}""".format(
                    partner_ids[0], company_id)
            self._cr.execute(query=query3)
            last_month_sales = self._cr.fetchall()
            previous_month_sales = last_month_sales[0][0]

            # Last Previous Month Sales
            if target_move == 'posted':
                query4 = """select COALESCE(sum(credit),0) from account_move_line where partner_id = {} and account_root_id=52048 and date between (select cast(date_trunc('month', current_date)-INTERVAL '1 MONTH'-INTERVAL '1 MONTH' as date)) and (select cast(date_trunc('month',
                                current_date)-INTERVAL '1 MONTH'-INTERVAL '1 MONTH'+INTERVAL '1 MONTH - 1 day' as date)) and parent_state = 'posted' and company_id = {}""".format(
                    partner_ids[0], company_id)
            else:
                query4 = """select COALESCE(sum(credit),0) from account_move_line where partner_id = {} and account_root_id=52048 and date between (select cast(date_trunc('month', current_date)-INTERVAL '1 MONTH'-INTERVAL '1 MONTH' as date)) and (select cast(date_trunc('month',
                                current_date)-INTERVAL '1 MONTH'-INTERVAL '1 MONTH'+INTERVAL '1 MONTH - 1 day' as date)) and company_id = {}""".format(
                    partner_ids[0], company_id)
            self._cr.execute(query=query4)
            bm_sales = self._cr.fetchall()
            last_before_month_sales = bm_sales[0][0]

            # Collection Amount From Month to Date(without openning balance)
            if branch_id:
                collection_amt_query = sum(value.amount for value in self.env['account.payment'].search([]))
                collection_amt_query = """select COALESCE(sum(amount),0::numeric) as amount from account_payment where partner_id = {} and  state='posted' and payment_date::date between '{}'::date and '{}'::date and branch_id = {} and company_id_new = {}""".format(
                    partner_ids[0], data['form']['date_from'], data['form']['date_to'], branch_id[0],
                    self.env.company.id)
            else:
                collection_amt_query = """select COALESCE(sum(amount),0::numeric) as amount from account_payment where partner_id = {} and  state='posted' and payment_date::date between '{}'::date and '{}'::date and company_id_new = {}""".format(
                    partner_ids[0], data['form']['date_from'], data['form']['date_to'], self.env.company.id)
            self._cr.execute(query=collection_amt_query)
            collection_amt_month_to_date_dt = self._cr.fetchall()
            collection_amt_month_to_date = collection_amt_month_to_date_dt[0][0]

            # Cheque amount in Sent mode
            if branch_id:
                query5 = """select COALESCE(sum(amount),0::numeric) as amount from  account_payment where partner_id = {} and  state='draft' or state = 'sent' and branch_id = {} and company_id_new = {} """.format(
                    partner_ids[0], branch_id[0], company_id)
            else:
                query5 = """select COALESCE(sum(amount),0::numeric) as amount from  account_payment where partner_id = {} and  state='draft' or state = 'sent' and company_id_new = {}""".format(
                    partner_ids[0], company_id)

            self._cr.execute(query=query5)
            check_in_hand = self._cr.fetchall()
            cheque_in_hand = check_in_hand[0][0]

            # Cheque amount in Dishonored mode
            if branch_id:
                query6 = """select COALESCE(sum(amount),0::numeric) as amount from account_payment where partner_id = {} and  state='dishonored' and branch_id = {} and company_id_new = {} """.format(
                    partner_ids[0], branch_id[0], company_id)
            else:
                query6 = """select COALESCE(sum(amount),0::numeric) as amount from account_payment where partner_id = {} and  state='dishonored' and company_id_new = {}""".format(
                    partner_ids[0], company_id)
            self._cr.execute(query=query6)
            dishonured_check = self._cr.fetchall()
            dishonored_cheque = dishonured_check[0][0]

            # Cheque amount in Draft mode
            if branch_id:
                coming_cheque = """
                                            select COALESCE(sum(amount),0::numeric) as amount from account_payment ap
                                            left join batch_payment bp on ap.batch_payment_id = bp.id
                                            where ap.partner_id = {} and ap.state not in ('posted', 'dishonored') 
                                            and (bp.state = 'approve' or bp.state is null)
                                            and ap.effective_date between CURRENT_DATE and CURRENT_DATE+15 and ap.branch_id = {} and company_id_new = {} """.format(
                    partner_ids[0], branch_id[0], company_id)
            else:
                coming_cheque = """
                                            select COALESCE(sum(amount),0::numeric) as amount from account_payment ap
                                            left join batch_payment bp on ap.batch_payment_id = bp.id
                                            where ap.partner_id = {} and ap.state not in ('posted', 'dishonored') 
                                            and (bp.state = 'approve' or bp.state is null)
                                            and ap.effective_date between CURRENT_DATE and CURRENT_DATE+15 and company_id_new = {}""".format(
                    partner_ids[0], company_id)

            self._cr.execute(query=coming_cheque)
            com_cheque = self._cr.fetchall()
            draft_cheque = com_cheque[0][0]
            #
            # # Cheque amount in Sent mode
            # clearing_cheque = """select COALESCE(sum(amount),0::numeric) as amount from account_payment where partner_id = {} and state='sent'""".format(partner_ids[0])
            # self._cr.execute(query=clearing_cheque)
            # clear_cheque = self._cr.fetchall()
            # sent_cheque = clear_cheque[0][0]

            # Cheque amount not in Posted and Canceled mode
            if branch_id:
                clearing_cheque = """
                            select COALESCE(sum(amount),0::numeric) as amount from account_payment where partner_id = {} and state not in ('posted', 'dishonored') 
                            and effective_date between CURRENT_DATE and CURRENT_DATE and branch_id = {} and company_id_new = {} """.format(
                    partner_ids[0], branch_id[0], company_id)
            else:
                clearing_cheque = """
                            select COALESCE(sum(amount),0::numeric) as amount from account_payment where partner_id = {} and state not in ('posted', 'dishonored') 
                            and effective_date between CURRENT_DATE and CURRENT_DATE and company_id_new = {} """.format(
                    partner_ids[0], company_id)
            self._cr.execute(query=clearing_cheque)
            clear_cheque = self._cr.fetchall()
            sent_cheque = clear_cheque[0][0]

            # In Word
            # words_val = num2words(self._sum_partner(data, partners[0],'debit - credit')+dishonured_check[0][0], lang='en').title()
            words_val = num2words(
                self._sum_partner(data, partners[0], 'debit - credit') + dishonured_check[0][0] + check_in_hand[0][0],
                lang='en').title()
            print(words_val)

            # Credit Limit Days
            payment_term_query = """select apt.name from ir_property ip left join res_partner rp on ip.res_id = concat('res.partner,',rp.id)
                    left join account_payment_term apt on ip.value_reference =concat('account.payment.term,',apt.id)
                    where ip.name like '%property_payment%' and {}""".format(where_pay_partner_ids)
            self._cr.execute(query=payment_term_query)
            payment_days = self._cr.fetchall()
            payment_day = 0
            if len(payment_days) > 0:
                payment_day = payment_days[0][0]
            else:
                payment_day = str('0 days')
            print('payment - ', payment_days)

        else:
            crLimit = 0.00
            current_month_sales = 0.00
            previous_month_sales = 0.00
            last_before_month_sales = 0.00
            cheque_in_hand = 0.00
            dishonored_cheque = 0.00
            draft_cheque = 0.00
            sent_cheque = 0.00
            words_val = 0.00
            payment_day = 0.00
            collection_amt_month_to_date = 0.00
        print('partners',partners)
        print('data[form][date_from]',data['form']['date_from'])
        print(data['form']['target_move'])
        print(data['form']['used_context']['branch_ids'])
        print('data is',data)

        report_name = 'Partner Ledger'

        filename = '%s' % (report_name)
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = utill.add_workbook_format(workbook=workbook)

        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:I3', report_name, wbf['title_doc'])
        column_group = [
            ('Company:', 27, 'char', 'no'),
            ('Date From:', 15, 'char', 'float'),
            ('Date To:', 15, 'char', 'float'),
            ('Target Moves:', 15, 'char', 'float'),
            ('Branch :', 20, 'char', 'float'),

        ]
        col = 0
        row = 4
        for column in column_group:
            column_name = column[0]
            column_width = column[1]
            worksheet.set_column(col,col,column_width)
            worksheet.write(row,col,column_name,wbf['header_orange'])
            col += 1
        row += 1
        col2 = 0
        worksheet.write(row,col2,data['form']['company_id'][1])
        col2 += 1
        worksheet.write(row,col2,str(data['form']['date_from']))
        col2 += 1
        worksheet.write(row,col2,str(data['form']['date_to']))
        col2 += 1
        if data['form']['target_move'] == 'all':
            worksheet.write(row,col2,'All Entries')
        if data['form']['target_move'] == 'posted':
            worksheet.write(row,col2,'All Posted Entries')
        col2 += 1
        if data['form']['branch_ids']['branch_ids']:
            worksheet.write(row,col2,data['form']['branch_ids']['branch_ids'][1])
        else:
            worksheet.write(row, col2, 'All Branches')
        row += 1
        column_data = [
            ('Date', 27, 'char', 'no'),
            ('JRNL', 15, 'char', 'float'),
            ('Ref', 15, 'char', 'float'),
            ('Remarks', 15, 'char', 'float'),
            ('Debit', 20, 'char', 'float'),
            ('Credit', 31, 'char', 'float'),
            ('Balance', 13, 'char', 'float'),
        ]
        col = 0
        for col_data in column_data:
            column_name = col_data[0]
            column_width = col_data[1]
            worksheet.set_column(col, col, column_width)
            worksheet.write(row, col, column_name, wbf['header_orange'])
            col += 1
        row += 1
        col = 0

        for partner in partners:
            if partner.ref:
                worksheet.merge_range('A%s:B%s' % (row+1 , row+1), partner.name)
                col += 2
                worksheet.write(row, col, partner.ref)
            else:
                worksheet.merge_range('A%s:C%s' % (row+1, row+1),partner.name)
            col += 2

            sum_partner1 = self._sum_partner(data, partner, "debit")
            sum_partner2 = self._sum_partner(data, partner, "credit")
            sum_partner3 = self._sum_partner(data, partner, 'debit - credit')

            print("sum_partner", sum_partner1)
            print("sum_partner2", sum_partner2)
            col += 2
            worksheet.write(row,col,sum_partner1)
            col += 1
            worksheet.write(row,col,sum_partner2)
            col += 1
            worksheet.write(row,col,sum_partner3)

            col3 = 0
            row += 1
            total_lines = self._lines(data,partner)
            print('total lines',total_lines)
            for line in total_lines:
                worksheet.write(row,col3,line['date'])
                col3 += 1
                worksheet.write(row,col3,line['code'])
                col3 += 1
                worksheet.write(row,col3,line['displayed_name'])
                col3 += 1
                worksheet.write(row,col3,line['remarks'])
                col3 += 1
                worksheet.write(row,col3,line['debit'])
                col3 += 1
                worksheet.write(row,col3,line['credit'])
                col3 += 1
                worksheet.write(row,col3,line['progress'])
                row += 1

            if is_mis_summery:
                row += 2
                worksheet.merge_range('C%s:D%s' % (row + 1, row + 1), 'MIS Summary', wbf['header_orange'])
                row += 1
                col4 = 0
                row2 = row
                worksheet.write(row, col4, 'Credit Limit(TK):')
                col4 += 1
                if crLimit:
                    worksheet.write(row, col4, crLimit)
                else:
                    worksheet.write(row, col4, '0.0 TK')
                # col4 += 3
                # worksheet.write(row, col4, 'Ledger value:')
                # col4 += 1
                # worksheet.write(row, col4, sum_partner3)
                row += 1

                col4 = 0
                worksheet.write(row,col4,'Credit Allowed Days:')
                col4 += 1
                worksheet.write(row,col4,payment_day)
                # col4 += 3
                # worksheet.write(row,col4,)

                row += 1
                col4 = 0
                worksheet.write(row,col4,'Security Money')
                col4 += 1
                worksheet.write(row,col4,security_money)

                row +=2
                col4 = 0
                worksheet.write(row,col4,'Sales',wbf['header_orange'])

                row += 1
                col4 = 0
                worksheet.write(row,col4,'Sales (Current Month):')
                col4 += 1
                if current_month_sales:
                    worksheet.write(row,col4,current_month_sales)
                else:
                    worksheet.write(row,col4,'0.0 TK')

                row += 1
                col4 = 0
                worksheet.write(row,col4,'Sales (Last Month)')
                col4 += 1
                worksheet.write(row,col4,previous_month_sales)

                row += 1
                col4 = 0
                worksheet.write(row, col4, 'Sales (Month Before the Last)')
                col4 += 1
                worksheet.write(row, col4, last_before_month_sales)

                row += 2
                col4 = 0
                worksheet.write(row, col4, 'Purchase', wbf['header_orange'])

                row += 1
                col4 = 0
                worksheet.write(row,col4,'Purchase (Month to Date):')
                col4 += 1
                worksheet.write(row,col4,'0.00 TK')

                row += 2
                col4 = 0
                worksheet.write(row,col4,'Collection',wbf['header_orange'])

                row += 1
                col4 = 0
                worksheet.write(row,col4,'Collection(Month to Date')
                col4 += 1
                worksheet.write(row,col4,collection_amt_month_to_date)
                row += 1
                worksheet.merge_range('C%s:D%s' % (row + 1, row + 1), 'Total Outstanding In Word:', wbf['header_orange'])
                col4 += 3
                if words_val:
                    worksheet.write(row,col4,words_val)
                else:
                    worksheet.write(row,col4,'Zero')


                col4 = 5
                worksheet.write(row2,col4,'Ledger value:')
                col4 += 1
                worksheet.write(row2,col4,sum_partner3)

                row2 += 2
                col4 = 5
                worksheet.write(row2,col4,'Ledger Information',wbf['header_orange'])

                row2 += 1
                worksheet.write(row2,col4,'Ledger value:')
                col4 += 1
                worksheet.write(row2,col4,sum_partner3)

                row2 += 1
                col4 = 5
                worksheet.write(row2,col4,'Cheque In Hand')
                col4 += 1
                worksheet.write(row2,col4,cheque_in_hand)

                row2 += 1
                col4 = 5
                worksheet.write(row2,col4,'Dishonored Cheque')
                col4 += 1
                worksheet.write(row2, col4, dishonored_cheque)

                row2 += 1
                col4 = 5
                worksheet.write(row2,col4,'Total Outstanding (Due):')
                col4 += 1
                if data['form']['target_move'] == 'posted':
                    worksheet.write(row2,col4,sum_partner3)
                if data['form']['target_move'] == 'all':
                    worksheet.write(row2,col4,sum_partner3 + cheque_in_hand)

                row2 += 2
                col4 = 5
                worksheet.write(row2,col4,'Cheque Information',wbf['header_orange'])

                row2 += 1
                col4 = 5
                worksheet.write(row2,col4,'Clearing Cheque:')
                col4 += 1
                worksheet.write(row2,col4,sent_cheque)

                row2 += 1
                col4 = 5
                worksheet.write(row2,col4,'Coming Cheque:')
                col4 += 1
                worksheet.write(row2,col4,draft_cheque)

                row2 += 1
                col4 = 5
                worksheet.write(row2,col4,'Collection Against Dishoured Cheque')
                col4 += 1
                worksheet.write(row2,col4,'0.0 Tk')






                # row2 += 1
                # col4 = 0
                # worksheet.write(row2,col4,)




                # return {
                #     'doc_ids': partner_ids,
                #     'doc_model': self.env['res.partner'],
                #     'data': data,
                #     'docs': partners,
                #     # 'time': time,
                #     'lines': self._lines,
                #     'sum_partner': self._sum_partner,
                #     'credit_limit': crLimit,
                #     'security_money': security_money,
                #     'current_month_sale': current_month_sales,
                #     'last_month_sale': previous_month_sales,
                #     'mb_sales': last_before_month_sales,
                #     'check_in_hand': cheque_in_hand,
                #     'dishonured_check': dishonored_cheque,
                #     'com_cheque': draft_cheque,
                #     'clear_cheque': sent_cheque,
                #     'words_val': words_val,
                #     'payment_days': payment_day,
                #     'is_mis': is_mis_summery,
                #     'collection_amt_month_to_date': collection_amt_month_to_date
                # }














        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'datas': out, 'datas_fname': filename})
        fp.close()
        filename += '%2Exlsx'

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=datas&download=true&filename=' + filename,
        }









        # col = 0
        # row = 4
        # print("data[2][0].name", self.company_id.name)
        # worksheet.write(row - 1, col, cloumn_group[0][0] + self.company_id.name, wbf['total_number'])
        # worksheet.write(row - 1, col + 2, cloumn_group[1][0] + str(data['form']['date_from']), wbf['total_number'])
        # worksheet.write(row, col + 2, cloumn_group[2][0] + str(data['form']['date_to']), wbf['total_number'])
        # if data['form']['target_move'] == 'all':
        #     worksheet.merge_range('E4:F4', cloumn_group[3][0] + "All Entries", wbf['total_number'])
        # if data['form']['target_move'] == 'posted':
        #     worksheet.merge_range('E4:F4', cloumn_group[3][0] + "All Posted Entries", wbf['total_number'])
        # worksheet.merge_range('H4:I4', cloumn_group[4][0], wbf['total_number'])
        #
        # for group in cloumn_group:
        #     # column_name1 = group[0]
        #     column_width = group[1]
        #     column_type = group[2]
        #     worksheet.set_column(col, col, column_width)
        #     # worksheet.write(row - 1, col, column_name1, wbf['header_green'])
        #     # worksheet.merge_range('A2:I3', column_name, wbf['header_orange'])
        #     col += 1
        #     # row += 1
        #
        # row += 1
        #
        # cloumn_group1 = [
        #     ('Date', 40, 'char', 'no'),
        #     ('JRNL', 30, 'char', 'char'),
        #     ('Account', 40, 'char', 'char'),
        #     ('Ref', 40, 'char', 'char'),
        #     ('Debit', 20, 'float', 'float'),
        #     ('Credit', 20, 'float', 'float'),
        #     ('Balance', 20, 'float', 'float'),
        #
        # ]
        # col1 = 0
        # for group1 in cloumn_group1:
        #     column_name1 = group1[0]
        #     column_width = group1[1]
        #     column_type = group1[2]
        #     worksheet.set_column(col1, col1, column_width)
        #     worksheet.write(row, col1, column_name1, wbf['header_orange'])
        #     # worksheet.merge_range('A2:I3', column_name, wbf['header_orange'])
        #     col1 += 1
        #     # row += 1
        #
        # row += 1
        # col2 = 0
        # row1 = 7
        # row2 = 8
        # # col3 = 0
        #
        # for o in dta['docs']:
        #     print("o.name", o.name)
        #     print("o.ref", o.ref)
        #     sum_partner1 = self._sum_partner(data, o, "debit")
        #     sum_partner2 = self._sum_partner(data, o, "credit")
        #     sum_partner3 = self._sum_partner(data, o, 'debit - credit')
        #     print("sum_partner", sum_partner1)
        #     print("sum_partner2", sum_partner2)
        #     worksheet.write(row1 - 1, col2, str(o.name), wbf['header_yellow'])
        #     # col2 +=1
        #     if not o.ref:
        #         print("ABCDE")
        #         worksheet.write(row1 - 1, col2 + 3, str(" "))
        #     else:
        #         worksheet.write(row1 - 1, col2 + 3, str(o.ref), wbf['total'])
        #     worksheet.write(row1 - 1, col2 + 4, str(sum_partner1), wbf['total'])
        #     worksheet.write(row1 - 1, col2 + 5, str(sum_partner2), wbf['total'])
        #     worksheet.write(row1 - 1, col2 + 6, str(sum_partner3), wbf['total'])
        #     # col2 += 1
        #
        #     # row2 = 8
        #     # col3=0
        #     lines1 = self._lines(data, o)
        #     print("lines1", lines1)
        #     for line in lines1:
        #         col3 = 0
        #         print("line", line)
        #         print("line['amount_currency']", line['amount_currency'])
        #         worksheet.write(row1, col3, str(line['date']))
        #         col3 += 1
        #         worksheet.write(row1, col3, str(line['code']))
        #         col3 += 1
        #         worksheet.write(row1, col3, str(line['a_code']))
        #         col3 += 1
        #         worksheet.write(row1, col3, str(line['displayed_name']))
        #         col3 += 1
        #         worksheet.write(row1, col3, str(line['debit']))
        #         col3 += 1
        #         worksheet.write(row1, col3, str(line['credit']))
        #         col3 += 1
        #         worksheet.write(row1, col3, str(line['progress']))
        #         row1 += 1
        #     row1 += 2
        #
        #     # row1+=1
        #
        # # for data in full_account1[0]['ref']:
        # #     print("data",data)
        #
        # workbook.close()
        # out = base64.encodestring(fp.getvalue())
        # self.write({'datas': out, 'datas_fname': filename})
        # fp.close()
        # filename += '%2Exlsx'
        # return {
        #     'type': 'ir.actions.act_url',
        #     'target': 'new',
        #     'url': 'web/content/?model=' + self._name + '&id=' + str(
        #         self.id) + '&field=datas&download=true&filename=' + filename,
        # }








        # return self.with_context(discard_logo_check=True)._print_report(data)

        # print('Yes here checked')
        # print('checked checked')
        # return self.with_context(discard_logo_check=True)._print_report(
        #     data)  # this '_print_report' is using here but not implemented,we inherit this model and override this method in every specific .py file

    # def excel_report(self):
    #     # print(self.read()[0])
    #     self.ensure_one()
    #     data = {}
    #     data['ids'] = self.env.context.get('active_ids', [])
    #     data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
    #     data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'company_id'])[0]
    #     used_context = self._build_contexts(data)
    #     print('used contex', used_context)
    #     data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
    #     data = self.pre_print_report(data)
    #     data['form'].update({'reconciled': self.reconciled, 'amount_currency': self.amount_currency,
    #                          'initial_balance': self.initial_balance})
    #     if data['form'].get('initial_balance') and not data['form'].get('date_from'):
    #         raise UserError(_("You must define a Start Date"))
    #     # data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
    #     # datas=self._report_values(data)
    #
    #     data['form'].update(self.read(['result_selection'])[0])
    #     data = self.pre_print_report(data)
    #     data['form'].update({'reconciled': self.reconciled, 'amount_currency': self.amount_currency,
    #                          'initial_balance': self.initial_balance})
    #     if data['form'].get('initial_balance') and not data['form'].get('date_from'):
    #         raise UserError(_("You must define a Start Date"))
    #     report_name = 'Partner Ledger'
    #     # print("data", data)
    #     dta = self._get_report_value(data)
    #     print('dta', dta)
    #


    def add_workbook_format(self, workbook):
        colors = {
            'white_orange': '#FFFFDB',
            'orange': '#FFC300',
            'red': '#FF0000',
            'yellow': '#F6FA03',
        }

        wbf = {}
        wbf['header'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': '#FFFFDB', 'font_color': '#000000', 'font_name': 'Georgia'})
        wbf['header'].set_border()


        wbf['header_orange'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': colors['orange'], 'font_color': '#000000',
             'font_name': 'Georgia'})
        wbf['header_orange'].set_border()

        wbf['header_yellow'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': colors['yellow'], 'font_color': '#000000',
             'font_name': 'Georgia'})
        wbf['header_yellow'].set_border()

        wbf['header_no'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': '#FFFFDB', 'font_color': '#000000', 'font_name': 'Georgia'})
        wbf['header_no'].set_border()
        wbf['header_no'].set_align('vcenter')

        wbf['footer'] = workbook.add_format({'align': 'left', 'font_name': 'Georgia'})

        wbf['content_datetime'] = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss', 'font_name': 'Georgia'})
        wbf['content_datetime'].set_left()
        wbf['content_datetime'].set_right()

        wbf['content_date'] = workbook.add_format({'num_format': 'yyyy-mm-dd', 'font_name': 'Georgia'})
        wbf['content_date'].set_left()
        wbf['content_date'].set_right()

        wbf['title_doc'] = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 20,
            'font_name': 'Georgia',
        })

        wbf['company'] = workbook.add_format({'align': 'left', 'font_name': 'Georgia'})
        wbf['company'].set_font_size(11)

        wbf['content'] = workbook.add_format()
        wbf['content'].set_left()
        wbf['content'].set_right()

        wbf['content_float'] = workbook.add_format(
            {'align': 'right', 'num_format': '#,##0.00', 'font_name': 'Georgia'})
        wbf['content_float'].set_right()
        wbf['content_float'].set_left()

        wbf['content_number'] = workbook.add_format(
            {'align': 'right', 'num_format': '#,##0', 'font_name': 'Georgia'})
        wbf['content_number'].set_right()
        wbf['content_number'].set_left()

        wbf['content_percent'] = workbook.add_format(
            {'align': 'right', 'num_format': '0.00%', 'font_name': 'Georgia'})
        wbf['content_percent'].set_right()
        wbf['content_percent'].set_left()

        wbf['total_float'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['white_orange'], 'align': 'right', 'num_format': '#,##0.00',
             'font_name': 'Georgia'})
        wbf['total_float'].set_top()
        wbf['total_float'].set_bottom()
        wbf['total_float'].set_left()
        wbf['total_float'].set_right()

        wbf['total_number'] = workbook.add_format(
            {'align': 'right', 'bg_color': colors['white_orange'], 'bold': 1, 'num_format': '#,##0',
             'font_name': 'Georgia'})
        wbf['total_number'].set_top()
        wbf['total_number'].set_bottom()
        wbf['total_number'].set_left()
        wbf['total_number'].set_right()

        wbf['total'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['white_orange'], 'align': 'center', 'font_name': 'Georgia'})
        wbf['total'].set_left()
        wbf['total'].set_right()
        wbf['total'].set_top()
        wbf['total'].set_bottom()

        wbf['total_float_yellow'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['yellow'], 'align': 'right', 'num_format': '#,##0.00',
             'font_name': 'Georgia'})
        wbf['total_float_yellow'].set_top()
        wbf['total_float_yellow'].set_bottom()
        wbf['total_float_yellow'].set_left()
        wbf['total_float_yellow'].set_right()

        wbf['total_number_yellow'] = workbook.add_format(
            {'align': 'right', 'bg_color': colors['yellow'], 'bold': 1, 'num_format': '#,##0',
             'font_name': 'Georgia'})
        wbf['total_number_yellow'].set_top()
        wbf['total_number_yellow'].set_bottom()
        wbf['total_number_yellow'].set_left()
        wbf['total_number_yellow'].set_right()

        wbf['total_yellow'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['yellow'], 'align': 'center', 'font_name': 'Georgia'})
        wbf['total_yellow'].set_left()
        wbf['total_yellow'].set_right()
        wbf['total_yellow'].set_top()
        wbf['total_yellow'].set_bottom()

        wbf['total_float_orange'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['orange'], 'align': 'right', 'num_format': '#,##0.00',
             'font_name': 'Georgia'})
        wbf['total_float_orange'].set_top()
        wbf['total_float_orange'].set_bottom()
        wbf['total_float_orange'].set_left()
        wbf['total_float_orange'].set_right()

        wbf['total_number_orange'] = workbook.add_format(
            {'align': 'right', 'bg_color': colors['orange'], 'bold': 1, 'num_format': '#,##0',
             'font_name': 'Georgia'})
        wbf['total_number_orange'].set_top()
        wbf['total_number_orange'].set_bottom()
        wbf['total_number_orange'].set_left()
        wbf['total_number_orange'].set_right()

        wbf['total_orange'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['orange'], 'align': 'center', 'font_name': 'Georgia'})
        wbf['total_orange'].set_left()
        wbf['total_orange'].set_right()
        wbf['total_orange'].set_top()
        wbf['total_orange'].set_bottom()

        wbf['header_detail_space'] = workbook.add_format({'font_name': 'Georgia'})
        wbf['header_detail_space'].set_left()
        wbf['header_detail_space'].set_right()
        wbf['header_detail_space'].set_top()
        wbf['header_detail_space'].set_bottom()

        wbf['header_detail'] = workbook.add_format({'bg_color': '#E0FFC2', 'font_name': 'Georgia'})
        wbf['header_detail'].set_left()
        wbf['header_detail'].set_right()
        wbf['header_detail'].set_top()
        wbf['header_detail'].set_bottom()

        return wbf, workbook


class AccountCommonPartnerReport(models.TransientModel):
    _inherit = "account.common.partner.report"

    branch_ids = fields.Many2one('res.branch', string='Branch')