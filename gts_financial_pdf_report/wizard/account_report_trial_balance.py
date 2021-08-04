# -*- coding: utf-8 -*-
import time
from odoo import api, models, _, fields
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, datetime, relativedelta, BytesIO, xlsxwriter, \
    base64
from custom_module.accounting_report.models.usl_xlxs_report_tools import UslXlxsReportUtil as utill


class AccountBalanceReport(models.TransientModel):
    _inherit = "account.common.account.report"
    _name = 'account.balance.report'
    _description = 'Trial Balance Report'

    def _get_accounts(self, accounts, display_account, from_date, company_id):
        print(company_id, accounts, display_account, from_date)
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
            start_date = datetime.strptime(str(from_date), DATE_FORMAT)
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

            #         print(m)
            #
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
        print('account res : ', account_res)
        return account_res

    def get_report_value(self, data=None):

        self.model = self.env.context.get('active_model')

        display_account = data['form'].get('display_account')
        accounts = self.env['account.account'].search([])
        company_id = data['form']['company_id']
        from_date = data['form']['date_from']
        account_res = self.with_context(data['form'].get('used_context'))._get_accounts(accounts, display_account,
                                                                                        from_date, company_id)

        return {

            'data': data['form'],

            'Accounts': account_res,
        }

    journal_ids = fields.Many2many('account.journal', 'account_balance_report_journal_rel', 'account_id', 'journal_id',
                                   string='Journals', required=True, default=[])

    def _print_report(self, data):
        data = self.pre_print_report(data)
        records = self.env[data['model']].browse(data.get('ids', []))
        return self.env.ref('gts_financial_pdf_report.action_report_trial_balance').report_action(records, data=data)

    def _print_excel_report(self, data):

        self.pre_print_report(data)
        data = self.get_report_value(data)
        report_name = self.env.user.company_id.name + " : " + 'Trail Balance Report'
        print(report_name)
        filename = '%s : %s' % (self.env.user.company_id.name, report_name)
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = utill.add_workbook_format(workbook=workbook)

        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:I3', report_name, wbf['title_doc'])
        worksheet.merge_range('A6:B6', 'Display Account', wbf['header_detail'])
        datas = data['data']
        display_account = None
        if datas['display_account'] == 'all':
            display_account = 'All accounts'
        elif datas['display_account'] == 'movement':
            display_account = 'With movements'
        elif datas['display_account'] == 'not_zero':
            display_account = 'With balance not equal to zero'

        worksheet.merge_range('A7:B7', display_account,
                              wbf['header_detail'])
        worksheet.write(5, 3, 'Date Form : ', wbf['header_detail'])
        worksheet.write(5, 4, str(datas['date_from']), wbf['header_detail'])
        worksheet.write(6, 3, 'Date Form : ', wbf['header_detail'])
        worksheet.write(6, 4, str(datas['date_from']), wbf['header_detail'])
        worksheet.merge_range('G6:H6', "Target Moves",
                              wbf['header_detail'])
        target_move = None
        if datas['target_move'] == 'all':
            target_move = 'All Entries'
        elif datas['target_move'] == 'posted':
            target_move = 'All Posted Entries'

        worksheet.merge_range('G7:H7', target_move,
                              wbf['header_detail'])
        worksheet.merge_range('J6:K6', "Branch",
                              wbf['header_detail'])
        if self.branch_ids:
            worksheet.merge_range('J7:K7', self.branch_ids.name,
                                  wbf['header_detail'])

        row = 10
        column_name = [
            ('Code', 15, 'char'),
            ('Account', 20, 'char'),
            ('Initial Balance', 20, 'char'),
            ('Debit', 20, 'char'),
            ('Credit', 20, 'char'),
            ('Balance', 20, 'char'),

        ]
        col = 0
        for column in column_name:
            column_name = column[0]
            column_width = column[1]
            worksheet.set_column(col, col, column_width)
            worksheet.write(row, col, column_name, wbf['header_orange'])
            col += 1
        row += 1
        accounts = data['Accounts']
        debit_total = 0
        credit_total = 0
        balance_total = 0
        for account in accounts:
            col = 0
            worksheet.write(row, col, account['code'])
            col += 1
            worksheet.write(row, col, account['name'])
            col += 1
            worksheet.write(row, col, account['initial_balance'])
            col += 1
            worksheet.write(row, col, account['debit'])
            col += 1
            worksheet.write(row, col, account['credit'])
            col += 1
            worksheet.write(row, col, account['balance'])
            debit_total += account['debit']
            credit_total += account['credit']
            balance_total += account['balance']
            col += 1
            row += 1
            worksheet.write(row, 0, 'Total', wbf['header_orange'])
            worksheet.write(row, 1, '', wbf['header_orange'])
            worksheet.write(row, 2, '', wbf['header_orange'])
            worksheet.write(row, 3, debit_total, wbf['header_orange'])
            worksheet.write(row, 4, credit_total, wbf['header_orange'])
            worksheet.write(row, 5, balance_total, wbf['header_orange'])

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


class AccountBalanceReport(models.TransientModel):
    _inherit = "account.balance.report"

    branch_ids = fields.Many2one('res.branch', string='Branch')
    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
