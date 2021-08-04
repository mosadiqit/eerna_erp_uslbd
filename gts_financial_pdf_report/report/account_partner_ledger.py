# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class ReportPartnerLedger(models.AbstractModel):
    _name = 'report.gts_financial_pdf_report.report_partnerledger'


    def _get_report_values(self, docids, data=None):
        # print('_get_report_values on report.gts_financial_pdf_report.report_partnerledger')

        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        data['computed'] = {}

        obj_partner = self.env['res.partner']

        query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        data['computed']['move_state'] = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            data['computed']['move_state'] = ['posted']
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
        reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".reconciled = false '
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
        self.env.cr.execute(query, tuple(params))
        partner_ids = [res['partner_id'] for res in self.env.cr.dictfetchall()]
        partners = obj_partner.browse(partner_ids)
        partners = sorted(partners, key=lambda x: (x.ref or '', x.name or ''))
        print("partners",partners)
        # return {
        #     'doc_ids': partner_ids,
        #     'doc_model': self.env['res.partner'],
        #     'data': data,
        #     'docs': partners,
        #     'time': time,
        #     'lines': self._lines,
        #     'name': 12000,
        #     'sum_partner': self._sum_partner,
        #     'credit_limit': 23550000.00,
        #     # 'result':self._partner_ledger,
        #     'partner_ledger':self.partner_ledger,
        #
        # }



    def _lines(self, data, partner):
        # print("data",data)
        # print("partner",partner)
        full_account = []
        company_id=data['form']['company_id'][0]
        currency = self.env['res.currency']
        print(company_id)

        # Initial Balance Calculation
        sum = 0.0
        init_balance = data['form'].get('initial_balance', True)
        if init_balance:
            init_query_get_data = self.env['account.move.line'].with_context(
                date_from=data['form'].get('date_from'), date_to=False, initial_bal=True,strict_range=True)._query_get()
            _init_params = [company_id,partner.id, tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + \
                           init_query_get_data[2]

            if data['form'].get('target_move') == 'all':
                # new_string=query_get_data[1].replace("date","date")
                new_string = init_query_get_data[1].replace('"account_move_line"."date"',
                                                            'case when ("account_move_line".collection_date is null) then "account_move_line"."date" ELSE "account_move_line".collection_date END')
                init_query_get_data = list(init_query_get_data)
                init_query_get_data.pop(1)
                init_query_get_data.insert(1, new_string)
                init_query_get_data = tuple(init_query_get_data)

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
                                    AND case when m.state = 'draft' then (m.is_draft_invoice is null or m.is_draft_invoice = false) else 1 = 1 end
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

        if data['form'].get('target_move') == 'all':
            # new_string=query_get_data[1].replace("date","date")
            new_string=query_get_data[1].replace('"account_move_line"."date"','case when ("account_move_line".collection_date is null) then "account_move_line"."date" ELSE "account_move_line".collection_date END')
            query_get_data=list(query_get_data)
            query_get_data.pop(1)
            query_get_data.insert(1,new_string)
            query_get_data=tuple(query_get_data)


        reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".reconciled = false '
        params = [company_id,partner.id, tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + query_get_data[2]
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
            WHERE m.company_id=%s AND "account_move_line".partner_id = %s AND case when m.state = 'draft' then (m.is_draft_invoice is null or m.is_draft_invoice = false) else 1 = 1 end
                AND m.state IN %s
                AND "account_move_line".account_id IN %s AND """ + query_get_data[1] + reconcile_clause + """
                ORDER BY "account_move_line".date, "account_move_line".id asc """

        if data['form'].get('target_move') == 'all':
            pass
        query = """
                        SELECT "account_move_line".id, case when ("account_move_line".collection_date is null) then "account_move_line".date ELSE "account_move_line".collection_date END as date, 
                        j.code, acc.code as a_code, acc.name as a_name, "account_move_line".ref,"account_move_line".move_id, 
                        CASE WHEN m.state = 'draft' THEN 'Draft' ELSE m.name END as move_name, 
                        "account_move_line".name, "account_move_line".debit, "account_move_line".credit, "account_move_line".amount_currency,"account_move_line".currency_id, c.symbol AS currency_code, so.note as remarks
                        FROM """ + query_get_data[0] + """
                        LEFT JOIN account_journal j ON ("account_move_line".journal_id = j.id)
                        LEFT JOIN account_account acc ON ("account_move_line".account_id = acc.id)
                        LEFT JOIN res_currency c ON ("account_move_line".currency_id=c.id)
                        LEFT JOIN account_move m ON (m.id="account_move_line".move_id)
            			LEFT JOIN sale_order so on (so.name=m.invoice_origin and so.company_id = m.company_id and m.type = 'out_invoice')
                        WHERE m.company_id=%s AND "account_move_line".partner_id = %s AND case when m.state = 'draft' then (m.is_draft_invoice is null or m.is_draft_invoice = false) else 1 = 1 end
                            AND m.state IN %s
                            AND "account_move_line".account_id IN %s AND """ + query_get_data[1] + reconcile_clause + """
                            ORDER BY "account_move_line".date, "account_move_line".id asc """
        self.env.cr.execute(query, tuple(params))
        res = self.env.cr.dictfetchall()
        #sum = 0.0
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
        print("full_account",full_account)
        return full_account

    def _sum_partner(self, data, partner, field):
        company_id=data['form']['company_id'][0]
        if field not in ['debit', 'credit', 'debit - credit']:
            return
        result = 0.0

        # query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()

        query_get_data = self.env['account.move.line'].with_context(
            date_from=False, date_to=False, initial_bal=False, strict_range=True)._query_get()

        # reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".reconciled = false '

        reconcile_clause = ' "account_move_line".reconciled = true '

        params = [company_id, partner.id, tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + query_get_data[2]



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
							AND CASE WHEN m.state = 'draft' THEN (m.is_draft_invoice is null or m.is_draft_invoice = false) ELSE 1 = 1 END
                            AND account_id IN %s
                            """


        self.env.cr.execute(query, tuple(params))

        contemp = self.env.cr.fetchone()
        print("contemp",contemp)
        if contemp is not None:
            result = contemp[0] or 0.0
        return result

