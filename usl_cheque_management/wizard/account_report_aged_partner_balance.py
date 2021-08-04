# -*- coding: utf-8 -*-

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountAgedTrialBalance(models.TransientModel):

    _name = 'aged.cheque_in_hand.trial.balance'
    _inherit = 'account.common.partner.report'
    _description = 'Account Aged Cheque In Hand Trial balance Report'

    def _get_default_journal(self):
        query = """
        select cheque_in_hand_account_id from saleotherexpense where company_id = {} limit 1""".format(self.env.user.company_id.id)
        self._cr.execute(query=query)
        query_result = self._cr.fetchall()
        if query_result:
            return self.env['account.journal'].search([('default_credit_account_id', '=', query_result[0][0])], limit=1).id

    period_length = fields.Integer(string='Period Length (days)', required=True, default=15)
    # journal_ids = fields.Many2many('account.journal', string='Journals', required=True, default=lambda self: self.load_draft_journal_id())

    journal_ids = fields.Many2one('account.journal', string='Journal', required=True, default=_get_default_journal)
    # journal_ids = fields.Many2one('account.journal', 'cheque_in_hand_aged_report_rel', 'cheque_in_hnad_aged_id',
    #                                'journal_ids', string='Journals', default=_get_default_journal)
    # journal_ids = fields.Many2many('account.journal', string='Journals', required=True)
    date_from = fields.Date(default=lambda *a: time.strftime('%Y-%m-%d'))

    @api.model
    def load_default_journal_id(self):
        # return self.env['account.journal'].browse(self._context.get('category_id'))
        query = """
                select id from account_journal where default_credit_account_id =
                    (select cheque_in_hand_account_id from saleotherexpense where company_id = {} limit 1) limit 1
                    """.format(self.env.user.company_id.id)
        self._cr.execute(query=query)
        query_result = self._cr.fetchall()
        if query_result:
            return query_result[0][0]

    def _print_report(self, data):
        res = {}
        data = self.pre_print_report(data)
        data['form'].update(self.read(['period_length'])[0])
        period_length = data['form']['period_length']
        if period_length<=0:
            raise UserError(_('You must set a period length greater than 0.'))
        if not data['form']['date_from']:
            raise UserError(_('You must set a start date.'))

        start = datetime.strptime(str(data['form']['date_from']), "%Y-%m-%d")

        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length - 1)
            res[str(i)] = {
                'name': (i!=0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
        data['form'].update(res)
        return self.env.ref('usl_cheque_management.action_report_aged_cheque_in_hand_balance').with_context(landscape=True).report_action(self, data=data)
