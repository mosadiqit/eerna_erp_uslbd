from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT


class CreditList(models.TransientModel):
    _name = 'credit.list.report'
    # _rec_name = 'name'
    # _description = 'New Description'

    start_date = fields.Date(string="Start Date", required=True, default=fields.Date.today)
    end_date = fields.Date(string="End Date", required=True, default=fields.Date.today)
    partner_id = fields.Many2many('res.partner', 'res_partner_credit_limit_rel', string='Customer')
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)

    def print_report(self):
        data = self.read()[0]
        product_ids = data['partner_id']
        company_id = data['company_id']
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.start_date, 'date_end': self.end_date, 'partner_id': self.partner_id.ids,
                'company_id': self.company_id.id
            },
        }

        return self.env.ref('accounting_report.account_credit_list_report').with_context(landscape=True).report_action(
            self, data=data)


class CreditListReport(models.AbstractModel):
    _name = 'report.accounting_report.credit_list_report_view'

    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        partner_ids = data['form']['partner_id']
        start_date = datetime.strptime(date_start, DATE_FORMAT)
        end_date = datetime.strptime(date_end, DATE_FORMAT)

        # account_payment_val = self.env['account.payment'].search([])
        # value = list()
        # credit_list = set()
        # for i in account_payment_val:
        #     if i.partner_id.name not in credit_list:
        #         credit_list.add(i.partner_id.name)
        #         val = {
        #         'partner_name':i.partner_id.name,
        #         }
        #     if i.state == 'dishonored':
        #         val['bounce'] = i.amount
        #     else:
        #         val['bounce'] = 0.0
        #     value.append(val)
        # print(value)
        where_partner_ids = "1=1"
        if partner_ids:
            where_partner_ids = " partner_id in %s" % str(tuple(partner_ids)).replace(',)', ')')
        query = """select partner_id,vw_credit_list.dealer_name,sum(bounce) as bounce,sum(ledgerdue) as ledgerdue,sum(cheque_in_hand) as cheque_in_hand,credit_limit,security_money,allow_days
                    from vw_credit_list
                    where {}
                    group by partner_id,dealer_name,credit_limit,security_money,allow_days order by partner_id asc""".format(where_partner_ids)
        print(query)
        self._cr.execute(query=query)
        credit_limit = self._cr.fetchall()
        return {
            'date_start': start_date,
            'date_end': end_date,
            'value': credit_limit
        }
