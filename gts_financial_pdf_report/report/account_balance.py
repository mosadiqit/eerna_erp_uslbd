# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, datetime, relativedelta
from datetime import date


class ReportTrialBalance(models.AbstractModel):
    _name = 'report.gts_financial_pdf_report.report_trialbalance'

    def _get_accounts(self, accounts, display_account, from_date, company_id):
        print(company_id)
        """ compute the balance, debit and credit for the provided accounts
            :Arguments:
                `accounts`: list of accounts record,
                `display_account`: it's used to display either all accounts or those accounts which balance is > 0
            :Returns a list of dictionary of Accounts with following key and value
                `name`: Account name,
                `code`: Account code,
                `credit`: total amount of credit,
                `debit`: total amount of debit,
                `balance`: total amount of balance,
        """

        account_result = {}
        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        tables = tables.replace('"', '')
        if not tables:
            tables = 'account_move_line'
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        # compute the balance, debit and credit forgit  the provided accounts
        request = (
                    "SELECT account_id AS id,0 as initial_balance, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" + \
                    " FROM " + tables + " WHERE  account_move_line.company_id= %s AND account_id IN %s " + filters + " GROUP BY account_id")
        params = (company_id[0], tuple(accounts.ids),) + tuple(where_params)
        self.env.cr.execute(request, params)
        for row in self.env.cr.dictfetchall():
            account_result[row.pop('id')] = row

        # Initial Balance Treatment start
        if from_date:
            start_date = datetime.strptime(from_date, DATE_FORMAT)
            account_result_ini = {}  # for initial balance
            # Initial Balance for trial Balance (add by raihan)
            request_ini = """SELECT account_id AS id,COALESCE((SUM(debit) - SUM(credit)),0) AS initial_balance
                             FROM {} WHERE  account_move_line.company_id= {} AND account_id IN {} and account_move_line.date< '{}' AND ("account_move_line"."move_id"="account_move_line__move_id"."id") AND ("account_move_line__move_id"."state" = 'posted') GROUP BY account_id""".format(
                tables, company_id[0], tuple(accounts.ids), start_date.strftime(DATETIME_FORMAT))

            self.env.cr.execute(request_ini)
            for init_row in self.env.cr.dictfetchall():
                account_result_ini[init_row.pop('id')] = init_row

            for m in account_result:
                for d in account_result_ini:
                    if m == d:
                        account_result[m]['initial_balance'] = account_result_ini[d].get('initial_balance')
                        break

                    # print(m)

            # print(account_result_ini)

        account_res = []
        for account in accounts:
            res = dict((fn, 0.0) for fn in ['initial_balance', 'credit', 'debit', 'balance'])
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res['code'] = account.code
            res['name'] = account.name
            if account.id in account_result:
                res['initial_balance'] = account_result[account.id].get('initial_balance')
                res['debit'] = account_result[account.id].get('debit')
                res['credit'] = account_result[account.id].get('credit')
                res['balance'] = account_result[account.id].get('balance')
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)
            if display_account == 'movement' and (
                    not currency.is_zero(res['debit']) or not currency.is_zero(res['credit'])):
                account_res.append(res)
        return account_res

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        display_account = data['form'].get('display_account')
        accounts = docs if self.model == 'account.account' else self.env['account.account'].search([])
        company_id = data['form']['company_id']
        from_date = data['form']['date_from']
        account_res = self.with_context(data['form'].get('used_context'))._get_accounts(accounts, display_account,
                                                                                        from_date, company_id)
        print('account res', account_res)
        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'Accounts': account_res,
        }
