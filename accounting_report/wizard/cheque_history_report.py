from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, datetime, relativedelta


class ChequeHistoryReport(models.TransientModel):
    _name = 'cheque.history.report'

    date_start = fields.Date(string='Start Collection Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Collection Date', required=True, default=fields.Date.today)
    location_ids = fields.Many2many('res.branch', string='Branch')
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),
                                 default=lambda self: self.env.user.company_id, required=True)

    def _get_companies(self):
        print(self.env.user)
        query = """select * from res_company_users_rel where user_id={}""".format(self.env.user.id)
        self._cr.execute(query=query)
        allowed_companies = self._cr.fetchall()
        print(allowed_companies)
        allowed_company = []
        for company in allowed_companies:
            allowed_company.append(company[0])
        return [('id', 'in', allowed_company)]

    def get_report(self):
        data = self.read()[0]
        date_start = data['date_start']  # start_date from the corresponding id
        date_end = data['date_end']
        location_ids = data['location_ids']
        company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),
                                     default=lambda self: self.env.user.company_id, required=True)

        where_company_id = "1=1"
        where_branch_ids = "1=1"

        if location_ids:
            where_branch_ids = " ap.branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        # if company_id:
        #     where_company_id = "am.company_id = {}".format(company_id[0])
        #     # where_supplier_wise_po = " rp.name = '%s'" % str(supplier_wise_po[1])
        #     print(where_company_id)

        query = """select ap.cheque_reference,ap.payment_date,ap.effective_date,bk.bank_name,ap.state,ap.cih_date,
                    ap.honor_date,ap.dishonor_date,ap.amount,rb.name 
                    from account_payment ap inner join res_branch rb on ap.branch_id = rb.id
                    inner join bank_info_all_bank bk on bk.id = ap.bank_id
                    where ap.payment_date::DATE between '{}' and '{}'
                    and {} and state in ('honored','dishonored') """.format(
            date_start.strftime(DATETIME_FORMAT), date_end.strftime(DATETIME_FORMAT),
            where_branch_ids)
        self._cr.execute(query)
        result = self._cr.fetchall()
        data = {
            'result': result,
            'date_start': date_start,
            'date_end': date_end,

        }
        return self.env.ref('accounting_report.cheque_history_report').report_action(
            self, data=data)


class ChequeHistoryReportGetValue(models.AbstractModel):
    _name = 'report.accounting_report.cheque_history_report_view'

    def _get_report_values(self, docids, data=None):
        print(' work here ')
        date_start = data['date_start']
        date_end = data['date_end']
        results = data['result']
        print(data)

        return {
            'group_value': results,
            'date_start': date_start,
            'date_end': date_end,
        }
