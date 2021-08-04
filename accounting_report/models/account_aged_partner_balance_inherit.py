import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, BytesIO, xlsxwriter, base64
from datetime import datetime
from dateutil.relativedelta import relativedelta
from custom_module.accounting_report.models.usl_xlxs_report_tools import UslXlxsReportUtil as utill


class ReportAgedPartnerBalanceInherit(models.Model):
    _name = "aged.partner.balance.inherit"
    _inherit = 'account.common.partner.report'

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    period_length = fields.Integer(string='Period Length (days)', required=True, default=30)
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True)
    date_from = fields.Date(default=lambda *a: time.strftime('%Y-%m-%d'))
    sales_person_ids = fields.Many2one('res.users', string='Sales Person', required=False)
    # domain=lambda self:self._get_configureDSa())
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),
                                 default=lambda self: self.env.user.company_id, required=True)
    partner_id=fields.Many2many('res.partner',string="Partner")

    def _get_partner_move_lines(self, account_type, date_from, target_move, period_length, sale_person_id,
                                sale_person_name, company_id,selected_partner_ids):
        # This method can receive the context key 'include_nullified_amount' {Boolean}
        # Do an invoice and a payment and unreconcile. The amount will be nullified
        # By default, the partner wouldn't appear in this report.
        # The context key allow it to appear
        # In case of a period_length of 30 days as of 2019-02-08, we want the following periods:
        # Name       Stop         Start
        # 1 - 30   : 2019-02-07 - 2019-01-09
        # 31 - 60  : 2019-01-08 - 2018-12-10
        # 61 - 90  : 2018-12-09 - 2018-11-10
        # 91 - 120 : 2018-11-09 - 2018-10-11
        # +120     : 2018-10-10
        ctx = self._context
        periods = {}
        date_from = fields.Date.from_string(date_from)
        start = date_from
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length)
            period_name = str((5 - (i + 1)) * period_length + 1) + '-' + str((5 - i) * period_length)
            period_stop = (start - relativedelta(days=1)).strftime('%Y-%m-%d')
            if i == 0:
                period_name = '+' + str(4 * period_length)
            periods[str(i)] = {
                'name': period_name,
                'stop': period_stop,
                'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop

        res = []
        total = []
        partner_clause = ''
        cr = self.env.cr
        user_company = self.env.company
        user_currency = user_company.currency_id
        company_ids = self._context.get('company_ids') or [user_company.id]
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type), date_from, date_from,)
        if 'partner_ids' in ctx:
            if ctx['partner_ids']:
                partner_clause = 'AND (l.partner_id IN %s)'
                arg_list += (tuple(ctx['partner_ids'].ids),)
            else:
                partner_clause = 'AND l.partner_id IS NULL'
        if ctx.get('partner_categories'):
            partner_clause += 'AND (l.partner_id IN %s)'
            partner_ids = self.env['res.partner'].search([('category_id', 'in', ctx['partner_categories'].ids)]).ids
            arg_list += (tuple(partner_ids or [0]),)
        arg_list += (date_from, tuple(company_ids))

        query = '''
               SELECT DISTINCT l.partner_id, res_partner.name AS name, UPPER(res_partner.name) AS UPNAME, CASE WHEN prop.value_text IS NULL THEN 'normal' ELSE prop.value_text END AS trust
               FROM account_move_line AS l
                 LEFT JOIN res_partner ON l.partner_id = res_partner.id
                 LEFT JOIN ir_property prop ON (prop.res_id = 'res.partner,'||res_partner.id AND prop.name='trust' AND prop.company_id=%s),
                 account_account, account_move am
               WHERE (l.account_id = account_account.id)
                   AND (l.move_id = am.id)
                   AND (am.state IN %s)
                   AND (account_account.internal_type IN %s)
                   AND (
                           l.reconciled IS NOT TRUE
                           OR l.id IN(
                               SELECT credit_move_id FROM account_partial_reconcile where max_date > %s
                               UNION ALL
                               SELECT debit_move_id FROM account_partial_reconcile where max_date > %s
                           )
                       )
                       ''' + partner_clause + '''
                   AND (l.date <= %s)
                   AND l.company_id IN %s
               ORDER BY UPPER(res_partner.name)'''
        arg_list = (self.env.company.id,) + arg_list
        cr.execute(query, arg_list)
        partners = cr.dictfetchall()
        # print(partners)
        # put a total of 0
        for i in range(7):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id'] for partner in partners]
        selected_partner = []
        if len(selected_partner_ids.ids) > 0:
            for selective in selected_partner_ids.ids:
                for all in partner_ids:
                    if selective == all:
                        selected_partner.append(selective)
            partner_ids.clear()
            partner_ids = selected_partner
        lines = dict((partner['partner_id'], []) for partner in partners)
        if not partner_ids:
            return [], [], {}

        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        for i in range(5):
            args_list = (tuple(move_state), tuple(account_type), tuple(partner_ids),)
            dates_query = '(COALESCE(l.date_maturity,l.date)'

            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s)'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (periods[str(i)]['stop'],)
            args_list += (date_from, tuple(company_ids))

            query = '''SELECT l.id
                       FROM account_move_line AS l, account_account, account_move am
                       WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                           AND (am.state IN %s)
                           AND (account_account.internal_type IN %s)
                           AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                           AND ''' + dates_query + '''
                       AND (l.date <= %s)
                       AND l.company_id IN %s
                       ORDER BY COALESCE(l.date_maturity, l.date)'''
            cr.execute(query, args_list)
            partners_amount = {}
            aml_ids = [x[0] for x in cr.fetchall()]
            # prefetch the fields that will be used; this avoid cache misses,
            # which look up the cache to determine the records to read, and has
            # quadratic complexity when the number of records is large...
            move_lines = self.env['account.move.line'].browse(aml_ids)
            move_lines._read(['partner_id', 'company_id', 'balance', 'matched_debit_ids', 'matched_credit_ids'])
            move_lines.matched_debit_ids._read(['max_date', 'company_id', 'amount'])
            move_lines.matched_credit_ids._read(['max_date', 'company_id', 'amount'])
            for line in move_lines:
                partner_id = line.partner_id.id or False
                if partner_id not in partners_amount:
                    partners_amount[partner_id] = 0.0
                line_amount = line.company_id.currency_id._convert(line.balance, user_currency, user_company, date_from)
                if user_currency.is_zero(line_amount):
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount += partial_line.company_id.currency_id._convert(partial_line.amount, user_currency,
                                                                                    user_company, date_from)
                for partial_line in line.matched_credit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount -= partial_line.company_id.currency_id._convert(partial_line.amount, user_currency,
                                                                                    user_company, date_from)

                if not self.env.company.currency_id.is_zero(line_amount):
                    partners_amount[partner_id] += line_amount
                    lines.setdefault(partner_id, [])
                    lines[partner_id].append({
                        'line': line,
                        'amount': line_amount,
                        'period': i + 1,
                    })

            history.append(partners_amount)

        # This dictionary will store the not due amount of all partners
        undue_amounts = {}
        query = '''SELECT l.id
                   FROM account_move_line AS l, account_account, account_move am
                   WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                       AND (am.state IN %s)
                       AND (account_account.internal_type IN %s)
                       AND (COALESCE(l.date_maturity,l.date) >= %s)\
                       AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                   AND (l.date <= %s)
                   AND l.company_id IN %s
                   ORDER BY COALESCE(l.date_maturity, l.date)'''
        cr.execute(query, (
            tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids)))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            partner_id = line.partner_id.id or False
            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            line_amount = line.company_id.currency_id._convert(line.balance, user_currency, user_company, date_from)
            if user_currency.is_zero(line_amount):
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.max_date <= date_from:
                    line_amount += partial_line.company_id.currency_id._convert(partial_line.amount, user_currency,
                                                                                user_company, date_from)
            for partial_line in line.matched_credit_ids:
                if partial_line.max_date <= date_from:
                    line_amount -= partial_line.company_id.currency_id._convert(partial_line.amount, user_currency,
                                                                                user_company, date_from)
            if not self.env.company.currency_id.is_zero(line_amount):
                undue_amounts[partner_id] += line_amount
                lines.setdefault(partner_id, [])
                lines[partner_id].append({
                    'line': line,
                    'amount': line_amount,
                    'period': 6,
                })

        for partner in partners:
            if partner['partner_id'] is None:
                partner['partner_id'] = False
            at_least_one_amount = False
            values = {}
            undue_amt = 0.0
            if partner['partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
                undue_amt = undue_amounts[partner['partner_id']]

            total[6] = total[6] + undue_amt
            values['direction'] = undue_amt
            if not float_is_zero(values['direction'], precision_rounding=self.env.company.currency_id.rounding):
                at_least_one_amount = True

            for i in range(5):
                during = False
                if partner['partner_id'] in history[i]:
                    during = [history[i][partner['partner_id']]]
                # Adding counter
                total[(i)] = total[(i)] + (during and during[0] or 0)
                values[str(i)] = during and during[0] or 0.0
                if not float_is_zero(values[str(i)], precision_rounding=self.env.company.currency_id.rounding):
                    at_least_one_amount = True
            values['total'] = sum([values['direction']] + [values[str(i)] for i in range(5)])
            # print(values['direction'])
            # print([values[str(i)] for i in range(5)])
            # Add for total
            total[(i + 1)] += values['total']
            values['partner_id'] = partner['partner_id']
            if partner['partner_id']:
                name = partner['name'] or ''
                values['name'] = len(name) >= 45 and name[0:40] + '...' or name
                values['trust'] = partner['trust']
            else:
                values['name'] = _('Unknown Partner')
                values['trust'] = False
                values['bp_amt'] = 0.0
                values['security_amt'] = 0.0
                values['tax_amt'] = 0.0
                values['vat_amt'] = 0.0

                grand_total = values['bp_amt'] + values['security_amt'] + values['tax_amt'] + values['vat_amt']

                values['grand_total_amt'] = grand_total

            # Start Adding BP and Security Money....................................................................................
            if partner['partner_id']:

                grand_total = 0
                # query = """
                #         select sum(credit) amount from account_move_line where partner_id = {}""".format(partner['partner_id'])
                isposted = ""
                if target_move == "posted":
                    isposted = "ml.parent_state ='posted' "
                else:
                    isposted = " 1=1 "
                # start previous done for static tax
                #     query = """
                #     select sum(ml.debit) debit, sum(ml.credit) credit, ml.name from account_move_line ml
                #     left join account_move m  on ml.move_id = m.id
                #     where ml.date >= '{}' and {} and ml.partner_id = {} and ml.company_id = {} and (ml.account_id in (536,534) or ml.tax_line_id in (select id from account_tax) ) group by ml.name
                #     """.format(date_from,isposted,partner['partner_id'],self.env.user.company_id.id)
                # end previous done for static tax
                #     print(sale_person_id)
                if sale_person_id == 0:
                    # start previous done for dynamic tax
                    # query = """
                    #     select sum(ml.debit) debit, sum(ml.credit) credit, ml.account_id from account_move_line ml
                    #     left join account_move m  on ml.move_id = m.id
                    #     where ml.date >= '{}' and {} and ml.partner_id = {} and ml.company_id = {} and
                    #     (ml.account_id in (select tax_received_account_id from saleotherexpense  where company_id = {})
                    #     or ml.account_id in (select vat_payable_account_id from saleotherexpense where company_id = {})
                    #     or ml.account_id in (select security_money_account_id from saleotherexpense where company_id = {})
                    #     or ml.account_id in (select bp_account_id from saleotherexpense  where company_id = {} )) group by ml.account_id
                    #     """.format(date_from, isposted, partner['partner_id'], company_id, company_id, company_id, company_id, company_id)
                    query = """
                           select sum(ml.debit) debit, sum(ml.credit) credit, ml.account_id from account_move_line ml
                           left join account_move m  on ml.move_id = m.id
                           where ml.date >= '{}' and {} and ml.partner_id = {} and ml.company_id = {} and 
                           (ml.account_id in (select tax_received_account_id from saleotherexpense  where company_id = {})
                           or ml.account_id in (select vat_payable_account_id from saleotherexpense where company_id = {}) 
                           or ml.account_id in (select bp_account_id from saleotherexpense  where company_id = {} )) group by ml.account_id

                            union all
                               select 0 as debit,sum(credit) as credit,(select security_money_account_id from saleotherexpense  where company_id = {}) from account_move_line where move_id in (
                           select move_id from account_move_line where account_id in (select security_money_account_id from saleotherexpense where company_id = {} and partner_id = {}) 
                           ) and account_root_id=49050
                           group by account_id
                           """.format(date_from, isposted, partner['partner_id'], company_id, company_id, company_id,
                                      company_id, company_id, company_id, company_id, partner['partner_id'])
                    # end previous done for dinamic tax
                else:
                    # query = """
                    #     select sum(ml.debit) debit, sum(ml.credit) credit, ml.account_id from account_move_line ml
                    #     left join account_move m  on ml.move_id = m.id
                    #     where ml.date >= '{}' and {} and ml.partner_id = {} and ml.company_id = {} and
                    #     (ml.account_id in (select tax_received_account_id from saleotherexpense  where company_id = {})
                    #     or ml.account_id in (select vat_payable_account_id from saleotherexpense where company_id = {})
                    #     or ml.account_id in (select security_money_account_id from saleotherexpense where company_id = {})
                    #     or ml.account_id in (select bp_account_id from saleotherexpense  where company_id = {} ))
                    #     and m.create_uid = {} group by ml.account_id
                    #     """.format(date_from, isposted, partner['partner_id'], company_id, company_id, company_id, company_id, company_id, sale_person_id)

                    query = """
                           select sum(ml.debit) debit, sum(ml.credit) credit, ml.account_id from account_move_line ml
                           left join account_move m  on ml.move_id = m.id
                           where ml.date >= '{}' and {} and ml.partner_id = {} and ml.company_id = {} and 
                           (ml.account_id in (select tax_received_account_id from saleotherexpense  where company_id = {})
                           or ml.account_id in (select vat_payable_account_id from saleotherexpense where company_id = {}) 
                           or ml.account_id in (select bp_account_id from saleotherexpense  where company_id = {} )) 
                           and m.create_uid = {} group by ml.account_id

                           union all
                               select 0 as debit,sum(credit) as credit,(select security_money_account_id from saleotherexpense  where company_id = {}) from account_move_line where move_id in (
                           select move_id from account_move_line where account_id in (select security_money_account_id from saleotherexpense where company_id = {} and partner_id = {}) 
                           ) and account_root_id=49050
                           group by account_id

                           """.format(date_from, isposted, partner['partner_id'], company_id,
                                      company_id, company_id, company_id, company_id, sale_person_id,
                                      company_id, company_id, partner['partner_id'])

                self._cr.execute(query=query)
                query_result = self._cr.fetchall()
                # print(query_result)
                print(query)
                # print(date_from)
                # print(isposted)
                # print(partner['partner_id'])

                query = """select tax_received_account_id, vat_payable_account_id, bp_account_id, security_money_account_id from saleotherexpense where company_id = {}""".format(
                    company_id)
                self._cr.execute(query=query)
                query_account_head_result = self._cr.fetchall()
                # print(query_account_head_result)
                # values['BP'] = query_result[0][0]
                values['bp_amt'] = 0.0
                values['security_amt'] = 0.0
                values['tax_amt'] = 0.0
                values['vat_amt'] = 0.0
                for o in query_result:
                    if o[2] == query_account_head_result[0][2]:
                        at_least_one_amount = True
                        values['bp_amt'] = o[1]
                    if o[2] != 0:
                        if o[2] == query_account_head_result[0][3]:
                            at_least_one_amount = True
                            values['security_amt'] = o[1] - o[0]
                    if o[2] != 0:
                        if o[2] == query_account_head_result[0][0]:
                            at_least_one_amount = True
                            values['tax_amt'] = o[1]
                    if o[2] != 0:
                        if o[2] == query_account_head_result[0][1]:
                            at_least_one_amount = True
                            values['vat_amt'] = o[1]
                # if list(filter(lambda query_result: query_result[2] == 'BP', query_result)):
                #     values['bp_amt'] = list(filter(lambda query_result: query_result == 'BP', query_result))[0][0] - list(filter(lambda query_result: query_result[2] == 'BP', query_result))[0][1]
                # if list(filter(lambda query_result: query_result[2] == 'SM' or query_result[2] == '', query_result)):
                #     values['security_amt'] = list(filter(lambda query_result: query_result[2] == 'SM' or query_result[2] == '', query_result))[1][0] - list(filter(lambda query_result: query_result[2] == 'SM' or query_result[2] == '', query_result))[1][1]
                # if list(filter(lambda query_result: query_result[2].contains('Tax'), query_result)):
                #     values['tax_amt'] = list(filter(lambda query_result: query_result[2].contains('Tax'), query_result))[0][1]
                # if list(filter(lambda query_result: query_result[2].str.contains('VAT'), query_result)):
                #     values['vat_amt'] = list(filter(lambda query_result: query_result[2].contains('VAT'), query_result))[0][1]

                # grand_total = values['bp_amt'] + values['security_amt'] + values['tax_amt'] + values['vat_amt']
                grand_total = values['total'] + values['bp_amt'] + values['security_amt'] + values['tax_amt'] + values[
                    'vat_amt']

                values['grand_total_amt'] = grand_total

            # End Adding BP and Security Money......................................................................................
            # print(at_least_one_amount)
            # print(lines[partner['partner_id']])
            # print(self._context.get('include_nullified_amount'))
            if at_least_one_amount or (self._context.get('include_nullified_amount') and lines[partner['partner_id']]):
                res.append(values)

        # print(res)

        return res, total, lines

    def _get_companies(self):
        query = """select * from res_company_users_rel where user_id={}""".format(self.env.user.id)
        self._cr.execute(query=query)
        allowed_companies = self._cr.fetchall()
        # print(allowed_companies)
        allowed_company = []
        for company in allowed_companies:
            allowed_company.append(company[0])
        return [('id', 'in', allowed_company)]

    # def check(self):
    #     return [('company_id', '=', self.env.company.id)]

    def _print_report(self, data):
        res = {}
        data = self.pre_print_report(data)
        data['form'].update(self.read(['period_length'])[0])
        data['form'].update(self.read(['sales_person_ids'])[0])
        data['form'].update(self.read(['company_id'])[0])
        period_length = data['form']['period_length']
        if period_length <= 0:
            raise UserError(_('You must set a period length greater than 0.'))
        if not data['form']['date_from']:
            raise UserError(_('You must set a start date.'))

        start = datetime.strptime(str(data['form']['date_from']), "%Y-%m-%d")

        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length - 1)
            res[str(i)] = {
                'name': (i != 0 and (str((5 - (i + 1)) * period_length) + '-' + str((5 - i) * period_length)) or (
                        '+' + str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
        data['form'].update(res)
        data['partner_ids']=self.partner_id

        return self.env.ref('accounting_report.report_agedpartnerbalance_details').with_context(
            landscape=True).report_action(self, data=data)

    def _print_excel_report(self, data):
        print('_print_excel_report')
        res = {}
        data = self.pre_print_report(data)
        data['form'].update(self.read(['period_length'])[0])
        data['form'].update(self.read(['sales_person_ids'])[0])
        data['form'].update(self.read(['company_id'])[0])
        period_length = data['form']['period_length']
        if period_length <= 0:
            raise UserError(_('You must set a period length greater than 0.'))
        if not data['form']['date_from']:
            raise UserError(_('You must set a start date.'))

        start = datetime.strptime(str(data['form']['date_from']), "%Y-%m-%d")

        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length - 1)
            res[str(i)] = {
                'name': (i != 0 and (str((5 - (i + 1)) * period_length) + '-' + str((5 - i) * period_length)) or (
                        '+' + str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
        data['form'].update(res)
        # if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
        #     raise UserError(_("Form content is missing, this report cannot be printed."))
        #
        # total = []
        # model = self.env.context.get('active_model')
        # docs = self.env[model].browse(self.env.context.get('active_id'))

        target_move = data['form'].get('target_move', 'all')
        date_from = fields.Date.from_string(data['form'].get('date_from')) or fields.Date.today()

        if data['form']['result_selection'] == 'customer':
            account_type = ['receivable']
        elif data['form']['result_selection'] == 'supplier':
            account_type = ['payable']
        else:
            account_type = ['payable', 'receivable']
        sale_person_id = 0
        sale_person_name = ""
        if data['form']['sales_person_ids']:
            sale_person_id = data['form']['sales_person_ids'][0]
            sale_person_name = data['form']['sales_person_ids'][1]
        selected_partner_ids=self.partner_id
        movelines, total, dummy = self._get_partner_move_lines(account_type, date_from, target_move,
                                                               data['form']['period_length'], sale_person_id,
                                                               sale_person_name, data['form']['company_id'][0],selected_partner_ids)
        # print(movelines)
        dt = {
            'doc_ids': self.ids,
            'data': data['form'],
            'time': time,
            'get_partner_lines': movelines,
            'get_direction': total,
            'sale_person_id': sale_person_id,
            'sale_person_name': sale_person_name,
            'company_id': self.env['res.company'].browse(
                data['form']['company_id'][0]),
        }
        report_name = 'Aged Partner Balance Details'

        filename = '%s' % (report_name)
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = utill.add_workbook_format(workbook=workbook)
        row = 6

        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:I3', report_name, wbf['title_doc'])
        worksheet.set_column(1, 13, 25)
        worksheet.write(row, 1, 'Start Date', wbf['header_orange'])
        worksheet.write(row, 2, str(dt['data']['date_from']), wbf['header_orange'])
        worksheet.write(row, 3, 'Period Length (days):', wbf['header_orange'])
        worksheet.write(row, 4, dt['data']['period_length'], wbf['header_orange'])
        row += 1
        worksheet.write(row, 1, 'Partner\'s:', wbf['header_orange'])
        data = dt['data']
        if data['result_selection'] == 'customer':
            worksheet.write(row, 2, 'Receivable Accounts', wbf['header_orange'])
        elif data['result_selection'] == 'supplier':
            worksheet.write(row, 2, 'Payable Accounts', wbf['header_orange'])
        elif data['result_selection'] == 'customer_supplier':
            worksheet.write(row, 2, 'Receivable and Payable Accounts', wbf['header_orange'])

        worksheet.write(row, 3, 'Target Moves: ', wbf['header_orange'])

        if data['target_move'] == 'all':
            worksheet.write(row, 4, 'All Entries', wbf['header_orange'])
        if data['target_move'] == 'posted':
            worksheet.write(row, 4, 'All Posted', wbf['header_orange'])
        row += 1
        worksheet.write(row, 1, 'Company : ', wbf['header_orange'])
        worksheet.write(row, 2, data['company_id'][1], wbf['header_orange'])
        row += 2

        if dt['sale_person_id'] != 0:
            worksheet.write(row, 1, 'Sales Person : ', wbf['header_orange'])
            worksheet.write(row, 2, dt['sale_person_name'], wbf['header_orange'])
            row += 1
        worksheet.write(row, 1, 'Partners', wbf['header_orange'])
        worksheet.write(row, 2, 'Not Due', wbf['header_orange'])
        worksheet.write(row, 3, data['4']['name'], wbf['header_orange'])
        worksheet.write(row, 4, data['3']['name'], wbf['header_orange'])
        worksheet.write(row, 5, data['2']['name'], wbf['header_orange'])
        worksheet.write(row, 6, data['1']['name'], wbf['header_orange'])
        worksheet.write(row, 7, data['0']['name'], wbf['header_orange'])
        worksheet.write(row, 8, 'Total Receivable Amt. ', wbf['header_orange'])
        worksheet.write(row, 9, 'Security Amt.', wbf['header_orange'])
        worksheet.write(row, 10, 'Tax Amt. ', wbf['header_orange'])
        worksheet.write(row, 11, 'BP Amt. ', wbf['header_orange'])
        worksheet.write(row, 12, 'VAT Amt.', wbf['header_orange'])
        worksheet.write(row, 13, 'Grand Total', wbf['header_orange'])
        row += 1
        get_direction = dt['get_direction']
        worksheet.write(row, 1, 'Account Total', wbf['header_orange'])
        worksheet.write(row, 2, get_direction[6], wbf['header_orange'])
        worksheet.write(row, 3, get_direction[4], wbf['header_orange'])
        worksheet.write(row, 4, get_direction[3], wbf['header_orange'])
        worksheet.write(row, 5, get_direction[2], wbf['header_orange'])
        worksheet.write(row, 6, get_direction[1], wbf['header_orange'])
        worksheet.write(row, 7, get_direction[0], wbf['header_orange'])
        worksheet.write(row, 8, get_direction[5], wbf['header_orange'])
        row += 1
        get_partner_lines = dt['get_partner_lines']
        for partner in get_partner_lines:
            worksheet.write(row, 1, partner['name'])
            worksheet.write(row, 2, partner['direction'])
            worksheet.write(row, 3, partner['4'])
            worksheet.write(row, 4, partner['3'])
            worksheet.write(row, 5, partner['2'])
            worksheet.write(row, 6, partner['1'])
            worksheet.write(row, 7, partner['0'])
            worksheet.write(row, 8, partner['total'])
            worksheet.write(row, 9, partner['security_amt'])
            worksheet.write(row, 10, partner['tax_amt'])
            worksheet.write(row, 11, partner['bp_amt'])
            worksheet.write(row, 12, partner['vat_amt'])
            worksheet.write(row, 13, partner['total'])

            row += 1

        # cloumn_product = [
        #     ('Cheque No', 10, 'char', 'no'),
        #     ('Date', 15, 'char', 'float'),
        #     ('Cheque Date', 20, 'char', 'float'),
        #     ('Bank Name', 39, 'char', 'float'),
        #     ('State', 20, 'char', 'float'),
        #     ('Honor Date', 29, 'char', 'float'),
        #     ('Cheque Amount', 29, 'char', 'float'),
        #
        # ]
        # row = 6
        # col = 0
        # for column in cloumn_product:
        #     column_name = column[0]
        #     column_width = column[1]
        #     column_type = column[2]
        #     worksheet.set_column(col, col, column_width)
        #     worksheet.write(row, col, column_name, wbf['header_orange'])
        #     col += 1
        # row += 1
        # grand_total = 0
        # for product in buyer_dict.keys():
        #     worksheet.merge_range('A%s:G%s' % (row, row), product, wbf['total_orange'])
        #     row += 1
        #     first_group_total = 0
        #     for second_goup in buyer_dict[product].keys():
        #         second_goup_total = 0
        #         worksheet.merge_range('A%s:G%s' % (row, row), second_goup, wbf['total_orange'])
        #         row += 1
        #         for cheque in buyer_dict[product][second_goup]:
        #             coll = 0
        #             for index, column in enumerate(cheque, start=2):
        #                 if index > 8:
        #                     break
        #                 # print(type(cheque[index]))
        #                 if isinstance(cheque[index], datetime.date):
        #                     print('come date time')
        #                     collm = str(cheque[index])
        #                     worksheet.write(row, coll, collm, wbf['header_orange'])
        #                 else:
        #                     worksheet.write(row, coll, cheque[index], wbf['header_orange'])
        #
        #                 coll += 1
        #             row += 1
        #             grand_total += cheque[8]
        #             first_group_total += cheque[8]
        #             second_goup_total += cheque[8]
        #         row += 1
        #         worksheet.merge_range('A%s:F%s' % (row, row), 'Customer Group Subtotal ', wbf['total_orange'])
        #         worksheet.write(row - 1, 6, second_goup_total, wbf['total_orange'])
        #         row += 1
        #     worksheet.merge_range('A%s:F%s' % (row, row), 'Buyer Group Subtotal ', wbf['total_orange'])
        #     worksheet.write(row - 1, 6, first_group_total, wbf['total_orange'])
        #     row += 1
        # worksheet.merge_range('A%s:F%s' % (row, row), 'Grand Total ', wbf['total_orange'])
        # worksheet.write(row - 1, 6, grand_total, wbf['total_orange'])
        # row += 1

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


class ReportAgedpartnerBalanceDetails(models.AbstractModel):
    _name = "report.accounting_report.report_agedpartnerbalance_details_view"

    def _get_partner_move_lines(self, account_type, date_from, target_move, period_length, sale_person_id,
                                sale_person_name, company_id,selected_partner_id):
        # This method can receive the context key 'include_nullified_amount' {Boolean}
        # Do an invoice and a payment and unreconcile. The amount will be nullified
        # By default, the partner wouldn't appear in this report.
        # The context key allow it to appear
        # In case of a period_length of 30 days as of 2019-02-08, we want the following periods:
        # Name       Stop         Start
        # 1 - 30   : 2019-02-07 - 2019-01-09
        # 31 - 60  : 2019-01-08 - 2018-12-10
        # 61 - 90  : 2018-12-09 - 2018-11-10
        # 91 - 120 : 2018-11-09 - 2018-10-11
        # +120     : 2018-10-10
        ctx = self._context
        periods = {}
        date_from = fields.Date.from_string(date_from)
        start = date_from
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length)
            period_name = str((5 - (i + 1)) * period_length + 1) + '-' + str((5 - i) * period_length)
            period_stop = (start - relativedelta(days=1)).strftime('%Y-%m-%d')
            if i == 0:
                period_name = '+' + str(4 * period_length)
            periods[str(i)] = {
                'name': period_name,
                'stop': period_stop,
                'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop

        res = []
        total = []
        partner_clause = ''
        cr = self.env.cr
        user_company = self.env.company
        user_currency = user_company.currency_id
        company_ids = self._context.get('company_ids') or [user_company.id]
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type), date_from, date_from,)
        if 'partner_ids' in ctx:
            if ctx['partner_ids']:
                partner_clause = 'AND (l.partner_id IN %s)'
                arg_list += (tuple(ctx['partner_ids'].ids),)
            else:
                partner_clause = 'AND l.partner_id IS NULL'
        if ctx.get('partner_categories'):
            partner_clause += 'AND (l.partner_id IN %s)'
            partner_ids = self.env['res.partner'].search([('category_id', 'in', ctx['partner_categories'].ids)]).ids
            arg_list += (tuple(partner_ids or [0]),)
        arg_list += (date_from, tuple(company_ids))

        query = '''
            SELECT DISTINCT l.partner_id, res_partner.name AS name, UPPER(res_partner.name) AS UPNAME, CASE WHEN prop.value_text IS NULL THEN 'normal' ELSE prop.value_text END AS trust
            FROM account_move_line AS l
              LEFT JOIN res_partner ON l.partner_id = res_partner.id
              LEFT JOIN ir_property prop ON (prop.res_id = 'res.partner,'||res_partner.id AND prop.name='trust' AND prop.company_id=%s),
              account_account, account_move am
            WHERE (l.account_id = account_account.id)
                AND (l.move_id = am.id)
                AND (am.state IN %s)
                AND (account_account.internal_type IN %s)
                AND (
                        l.reconciled IS NOT TRUE
                        OR l.id IN(
                            SELECT credit_move_id FROM account_partial_reconcile where max_date > %s
                            UNION ALL
                            SELECT debit_move_id FROM account_partial_reconcile where max_date > %s
                        )
                    )
                    ''' + partner_clause + '''
                AND (l.date <= %s)
                AND l.company_id IN %s
            ORDER BY UPPER(res_partner.name)'''
        arg_list = (self.env.company.id,) + arg_list
        cr.execute(query, arg_list)
        partners = cr.dictfetchall()
        # print(partners)
        # put a total of 0
        for i in range(7):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id'] for partner in partners]
        # if isinstance(selected_partner_ids,'obj'):
        selected_partner = []
        if len(selected_partner_id) > 0:
            for selective in selected_partner_id:
                for all in partner_ids:
                    if selective == all:
                        selected_partner.append(selective)
            partner_ids.clear()
            partner_ids = selected_partner
        # selected_partner = []
        # if len(selected_partner_ids) > 0:
        #     for selective in selected_partner_ids:
        #         for all in partner_ids:
        #             if selective == all:
        #                 selected_partner.append(selective)
        #     partner_ids.clear()
        #     partner_ids = selected_partner
        lines = dict((partner['partner_id'], []) for partner in partners)
        if not partner_ids:
            return [], [], {}

        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        for i in range(5):
            args_list = (tuple(move_state), tuple(account_type), tuple(partner_ids),)
            dates_query = '(COALESCE(l.date_maturity,l.date)'

            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s)'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (periods[str(i)]['stop'],)
            args_list += (date_from, tuple(company_ids))

            query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.internal_type IN %s)
                        AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                        AND ''' + dates_query + '''
                    AND (l.date <= %s)
                    AND l.company_id IN %s
                    ORDER BY COALESCE(l.date_maturity, l.date)'''
            cr.execute(query, args_list)
            partners_amount = {}
            aml_ids = [x[0] for x in cr.fetchall()]
            # prefetch the fields that will be used; this avoid cache misses,
            # which look up the cache to determine the records to read, and has
            # quadratic complexity when the number of records is large...
            move_lines = self.env['account.move.line'].browse(aml_ids)
            move_lines._read(['partner_id', 'company_id', 'balance', 'matched_debit_ids', 'matched_credit_ids'])
            move_lines.matched_debit_ids._read(['max_date', 'company_id', 'amount'])
            move_lines.matched_credit_ids._read(['max_date', 'company_id', 'amount'])
            for line in move_lines:
                partner_id = line.partner_id.id or False
                if partner_id not in partners_amount:
                    partners_amount[partner_id] = 0.0
                line_amount = line.company_id.currency_id._convert(line.balance, user_currency, user_company, date_from)
                if user_currency.is_zero(line_amount):
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount += partial_line.company_id.currency_id._convert(partial_line.amount, user_currency,
                                                                                    user_company, date_from)
                for partial_line in line.matched_credit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount -= partial_line.company_id.currency_id._convert(partial_line.amount, user_currency,
                                                                                    user_company, date_from)

                if not self.env.company.currency_id.is_zero(line_amount):
                    partners_amount[partner_id] += line_amount
                    lines.setdefault(partner_id, [])
                    lines[partner_id].append({
                        'line': line,
                        'amount': line_amount,
                        'period': i + 1,
                    })

            history.append(partners_amount)

        # This dictionary will store the not due amount of all partners
        undue_amounts = {}
        query = '''SELECT l.id
                FROM account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.internal_type IN %s)
                    AND (COALESCE(l.date_maturity,l.date) >= %s)\
                    AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                AND (l.date <= %s)
                AND l.company_id IN %s
                ORDER BY COALESCE(l.date_maturity, l.date)'''
        cr.execute(query, (
            tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids)))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            partner_id = line.partner_id.id or False
            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            line_amount = line.company_id.currency_id._convert(line.balance, user_currency, user_company, date_from)
            if user_currency.is_zero(line_amount):
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.max_date <= date_from:
                    line_amount += partial_line.company_id.currency_id._convert(partial_line.amount, user_currency,
                                                                                user_company, date_from)
            for partial_line in line.matched_credit_ids:
                if partial_line.max_date <= date_from:
                    line_amount -= partial_line.company_id.currency_id._convert(partial_line.amount, user_currency,
                                                                                user_company, date_from)
            if not self.env.company.currency_id.is_zero(line_amount):
                undue_amounts[partner_id] += line_amount
                lines.setdefault(partner_id, [])
                lines[partner_id].append({
                    'line': line,
                    'amount': line_amount,
                    'period': 6,
                })

        for partner in partners:
            if partner['partner_id'] is None:
                partner['partner_id'] = False
            at_least_one_amount = False
            values = {}
            undue_amt = 0.0
            if partner['partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
                undue_amt = undue_amounts[partner['partner_id']]

            total[6] = total[6] + undue_amt
            values['direction'] = undue_amt
            if not float_is_zero(values['direction'], precision_rounding=self.env.company.currency_id.rounding):
                at_least_one_amount = True

            for i in range(5):
                during = False
                if partner['partner_id'] in history[i]:
                    during = [history[i][partner['partner_id']]]
                # Adding counter
                total[(i)] = total[(i)] + (during and during[0] or 0)
                values[str(i)] = during and during[0] or 0.0
                if not float_is_zero(values[str(i)], precision_rounding=self.env.company.currency_id.rounding):
                    at_least_one_amount = True
            values['total'] = sum([values['direction']] + [values[str(i)] for i in range(5)])
            # print(values['direction'])
            # print([values[str(i)] for i in range(5)])
            # Add for total
            total[(i + 1)] += values['total']
            values['partner_id'] = partner['partner_id']
            if partner['partner_id']:
                name = partner['name'] or ''
                values['name'] = len(name) >= 45 and name[0:40] + '...' or name
                values['trust'] = partner['trust']
            else:
                values['name'] = _('Unknown Partner')
                values['trust'] = False
                values['bp_amt'] = 0.0
                values['security_amt'] = 0.0
                values['tax_amt'] = 0.0
                values['vat_amt'] = 0.0

                grand_total = values['bp_amt'] + values['security_amt'] + values['tax_amt'] + values['vat_amt']

                values['grand_total_amt'] = grand_total

            # Start Adding BP and Security Money....................................................................................
            if partner['partner_id']:

                grand_total = 0
                # query = """
                #         select sum(credit) amount from account_move_line where partner_id = {}""".format(partner['partner_id'])
                isposted = ""
                if target_move == "posted":
                    isposted = "ml.parent_state ='posted' "
                else:
                    isposted = " 1=1 "
                # start previous done for static tax
                #     query = """
                #     select sum(ml.debit) debit, sum(ml.credit) credit, ml.name from account_move_line ml
                #     left join account_move m  on ml.move_id = m.id
                #     where ml.date >= '{}' and {} and ml.partner_id = {} and ml.company_id = {} and (ml.account_id in (536,534) or ml.tax_line_id in (select id from account_tax) ) group by ml.name
                #     """.format(date_from,isposted,partner['partner_id'],self.env.user.company_id.id)
                # end previous done for static tax
                #     print(sale_person_id)
                if sale_person_id == 0:
                    # start previous done for dynamic tax
                    # query = """
                    #     select sum(ml.debit) debit, sum(ml.credit) credit, ml.account_id from account_move_line ml
                    #     left join account_move m  on ml.move_id = m.id
                    #     where ml.date >= '{}' and {} and ml.partner_id = {} and ml.company_id = {} and
                    #     (ml.account_id in (select tax_received_account_id from saleotherexpense  where company_id = {})
                    #     or ml.account_id in (select vat_payable_account_id from saleotherexpense where company_id = {})
                    #     or ml.account_id in (select security_money_account_id from saleotherexpense where company_id = {})
                    #     or ml.account_id in (select bp_account_id from saleotherexpense  where company_id = {} )) group by ml.account_id
                    #     """.format(date_from, isposted, partner['partner_id'], company_id, company_id, company_id, company_id, company_id)
                    query = """
                        select sum(ml.debit) debit, sum(ml.credit) credit, ml.account_id from account_move_line ml
                        left join account_move m  on ml.move_id = m.id
                        where ml.date >= '{}' and {} and ml.partner_id = {} and ml.company_id = {} and 
                        (ml.account_id in (select tax_received_account_id from saleotherexpense  where company_id = {})
                        or ml.account_id in (select vat_payable_account_id from saleotherexpense where company_id = {}) 
                        or ml.account_id in (select bp_account_id from saleotherexpense  where company_id = {} )) group by ml.account_id

                         union all
                            select 0 as debit,sum(credit) as credit,(select security_money_account_id from saleotherexpense  where company_id = {}) from account_move_line where move_id in (
                        select move_id from account_move_line where account_id in (select security_money_account_id from saleotherexpense where company_id = {} and partner_id = {}) 
                        ) and account_root_id=49050
                        group by account_id
                        """.format(date_from, isposted, partner['partner_id'], company_id, company_id, company_id,
                                   company_id, company_id, company_id, company_id, partner['partner_id'])
                    # end previous done for dinamic tax
                else:
                    # query = """
                    #     select sum(ml.debit) debit, sum(ml.credit) credit, ml.account_id from account_move_line ml
                    #     left join account_move m  on ml.move_id = m.id
                    #     where ml.date >= '{}' and {} and ml.partner_id = {} and ml.company_id = {} and
                    #     (ml.account_id in (select tax_received_account_id from saleotherexpense  where company_id = {})
                    #     or ml.account_id in (select vat_payable_account_id from saleotherexpense where company_id = {})
                    #     or ml.account_id in (select security_money_account_id from saleotherexpense where company_id = {})
                    #     or ml.account_id in (select bp_account_id from saleotherexpense  where company_id = {} ))
                    #     and m.create_uid = {} group by ml.account_id
                    #     """.format(date_from, isposted, partner['partner_id'], company_id, company_id, company_id, company_id, company_id, sale_person_id)

                    query = """
                        select sum(ml.debit) debit, sum(ml.credit) credit, ml.account_id from account_move_line ml
                        left join account_move m  on ml.move_id = m.id
                        where ml.date >= '{}' and {} and ml.partner_id = {} and ml.company_id = {} and 
                        (ml.account_id in (select tax_received_account_id from saleotherexpense  where company_id = {})
                        or ml.account_id in (select vat_payable_account_id from saleotherexpense where company_id = {}) 
                        or ml.account_id in (select bp_account_id from saleotherexpense  where company_id = {} )) 
                        and m.create_uid = {} group by ml.account_id

                        union all
                            select 0 as debit,sum(credit) as credit,(select security_money_account_id from saleotherexpense  where company_id = {}) from account_move_line where move_id in (
                        select move_id from account_move_line where account_id in (select security_money_account_id from saleotherexpense where company_id = {} and partner_id = {}) 
                        ) and account_root_id=49050
                        group by account_id

                        """.format(date_from, isposted, partner['partner_id'], company_id,
                                   company_id, company_id, company_id, company_id, sale_person_id,
                                   company_id, company_id, partner['partner_id'])

                self._cr.execute(query=query)
                query_result = self._cr.fetchall()
                # print(query_result)
                print(query)
                # print(date_from)
                # print(isposted)
                # print(partner['partner_id'])

                query = """select tax_received_account_id, vat_payable_account_id, bp_account_id, security_money_account_id from saleotherexpense where company_id = {}""".format(
                    company_id)
                self._cr.execute(query=query)
                query_account_head_result = self._cr.fetchall()
                # print(query_account_head_result)
                # values['BP'] = query_result[0][0]
                values['bp_amt'] = 0.0
                values['security_amt'] = 0.0
                values['tax_amt'] = 0.0
                values['vat_amt'] = 0.0
                for o in query_result:
                    if o[2] == query_account_head_result[0][2]:
                        at_least_one_amount = True
                        values['bp_amt'] = o[1]
                    if o[2] != 0:
                        if o[2] == query_account_head_result[0][3]:
                            at_least_one_amount = True
                            values['security_amt'] = o[1] - o[0]
                    if o[2] != 0:
                        if o[2] == query_account_head_result[0][0]:
                            at_least_one_amount = True
                            values['tax_amt'] = o[1]
                    if o[2] != 0:
                        if o[2] == query_account_head_result[0][1]:
                            at_least_one_amount = True
                            values['vat_amt'] = o[1]
                # if list(filter(lambda query_result: query_result[2] == 'BP', query_result)):
                #     values['bp_amt'] = list(filter(lambda query_result: query_result == 'BP', query_result))[0][0] - list(filter(lambda query_result: query_result[2] == 'BP', query_result))[0][1]
                # if list(filter(lambda query_result: query_result[2] == 'SM' or query_result[2] == '', query_result)):
                #     values['security_amt'] = list(filter(lambda query_result: query_result[2] == 'SM' or query_result[2] == '', query_result))[1][0] - list(filter(lambda query_result: query_result[2] == 'SM' or query_result[2] == '', query_result))[1][1]
                # if list(filter(lambda query_result: query_result[2].contains('Tax'), query_result)):
                #     values['tax_amt'] = list(filter(lambda query_result: query_result[2].contains('Tax'), query_result))[0][1]
                # if list(filter(lambda query_result: query_result[2].str.contains('VAT'), query_result)):
                #     values['vat_amt'] = list(filter(lambda query_result: query_result[2].contains('VAT'), query_result))[0][1]

                # grand_total = values['bp_amt'] + values['security_amt'] + values['tax_amt'] + values['vat_amt']
                grand_total = values['total'] + values['bp_amt'] + values['security_amt'] + values['tax_amt'] + values[
                    'vat_amt']

                values['grand_total_amt'] = grand_total

            # End Adding BP and Security Money......................................................................................
            # print(at_least_one_amount)
            # print(lines[partner['partner_id']])
            # print(self._context.get('include_nullified_amount'))
            if at_least_one_amount or (self._context.get('include_nullified_amount') and lines[partner['partner_id']]):
                res.append(values)

        # print(res)

        return res, total, lines

    @api.model
    def _get_report_values(self, docids, data=None):

        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))

        target_move = data['form'].get('target_move', 'all')
        date_from = fields.Date.from_string(data['form'].get('date_from')) or fields.Date.today()
        partners = data['partner_ids']

        new_partner_ids = []
        x = partners.split("(")
        y = x[1].split(")")
        z = y[0].split(",")
        if z[0] != '':
            new_partner_ids = [int(x) for x in z if x != '']

        if data['form']['result_selection'] == 'customer':
            account_type = ['receivable']
        elif data['form']['result_selection'] == 'supplier':
            account_type = ['payable']
        else:
            account_type = ['payable', 'receivable']
        sale_person_id = 0
        sale_person_name = ""
        if data['form']['sales_person_ids']:
            sale_person_id = data['form']['sales_person_ids'][0]
            sale_person_name = data['form']['sales_person_ids'][1]

        movelines, total, dummy = self._get_partner_move_lines(account_type, date_from, target_move,
                                                               data['form']['period_length'], sale_person_id,
                                                               sale_person_name, data['form']['company_id'][0],new_partner_ids)
        # print(movelines)
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_partner_lines': movelines,
            'get_direction': total,
            'sale_person_id': sale_person_id,
            'sale_person_name': sale_person_name,
            'company_id': self.env['res.company'].browse(
                data['form']['company_id'][0]),
        }
