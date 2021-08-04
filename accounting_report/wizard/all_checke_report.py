from datetime import datetime

from odoo import fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class AllChequeReport(models.TransientModel):
    _name = 'all.cheque.report.wizard'
    _description = 'AllChequeReport'

    def _get_companies(self):
        query = """select * from res_company_users_rel where user_id={}""".format(self.env.user.id)
        self._cr.execute(query=query)
        allowed_companies = self._cr.fetchall()
        allowed_company = []

        for company in allowed_companies:
            allowed_company.append(company[0])
        return [('id', 'in', allowed_company)]

    query_dictionary = {
        'accounting_report.in_hand_report': """ 
                    select ap.partner_type,rp.name,ap.check_number,ap.payment_date,ap.effective_date,ap.bank_reference,ap.state,
                    ap.honor_date,amount,rb.name from account_payment ap left join res_partner rp on ap.partner_id=rp.id
                    left join res_branch rb on ap.branch_id = rb.id
                    where ap.payment_date::DATE between '{}' and '{}' and {} and {} and {} and ap.state='draft'
                    """,
        'accounting_report.branchwise_report': """ 
                    select aj.name,cheque_reference,payment_date,rp.name,bank_reference,state,effective_date,amount from account_payment as ap 
                    left join res_partner as rp on ap.partner_id = rp.id 
                    left join account_journal as aj on ap.journal_id=aj.id
                    where ap.state='sent' and ap.payment_date::DATE between '{}' and '{}' and {} and {} and {}
                    """,
        'accounting_report.collected_cheque_without_treatment_report': """select rp.name as a_customer,ap.cheque_reference as a_cheque_number,ap.payment_date as a_rec_date,
                ap.effective_date as a_cheque_date,ap.bank_reference as a_bank_name,ap.name as a_collection_no,
                he.name as a_sales_p,ap.amount as a_amount,rpc.name as a_group, rb.name from
                account_payment ap inner join res_partner rp on ap.partner_id=rp.id
                left join account_move am on am.name=ap.communication
                left join res_branch rb on ap.branch_id = rb.id
                left join sale_order sl on sl.name=am.invoice_origin
                left join res_users ru on ru.id=sl.create_uid
                left join hr_employee he on he.user_id = ru.id
                left join res_partner_res_partner_category_rel as rl on am.partner_id = rl.partner_id
                left join res_partner_category rpc on rpc.id = rl.category_id
                where ap.payment_date::DATE between '{}' and '{}'
                and {} and {} and {} and {}""",
        'accounting_report.collection_against_dishonor_cheque': """select rb.name as branch, rp.name as customer,ap.bank_reference,ap.check_number,ap.payment_date,ap.effective_date,ap.amount from account_payment as ap
    left join res_partner as rp on ap.partner_id = rp.id
    left join res_branch as rb on ap.branch_id=rb.id
    where ap.state = 'posted' and ap.dishonor_count >0 and ap.payment_date::DATE between '{}'and '{}' and {} and {} and {}""",
    }

    cheque_report_list = [('accounting_report.in_hand_report', 'Cheque In Hand'),
                          ('accounting_report.branchwise_report', 'Cheque Send Report'),
                          ('accounting_report.collected_cheque_without_treatment_report',
                           'Collected Cheque With out Treatment'),
                          (
                              'accounting_report.collection_against_dishonor_cheque',
                              'Collection Against Dishonor Cheque'),
                          ('accounting_report.Cheque_dishonored_report', 'Cheque Dishonored Report'),
                          ('accounting_report.Cheque_honored_report', 'Cheque honored Report')]
    report_model_dict = {
        'accounting_report.in_hand_report': 'cheque.in.hand.report.wizard'
    }

    def get_report(self):
        data = self.read()[0]

        where_customer_ids = "1=1"
        where_branch_ids = "1=1"
        where_company_id = "1=1"
        where_group_id = '1=1'
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        branch_ids = data.get('branch_ids')
        customer = data.get('customer_ids')
        company_id = data.get('company_id')
        select_report = data.get('select_cheque_report')
        if branch_ids:
            where_branch_ids = " ap.branch_id in %s" % str(tuple(branch_ids)).replace(',)', ')')
        if customer:
            where_customer_ids = " ap.partner_id in %s" % str(tuple(customer)).replace(',)', ')')

        if company_id and select_report != 'accounting_report.branchwise_report':
            where_company_id = " rb.company_id = {}".format(company_id[0])
        else:
            where_company_id = " aj.company_id = {}".format(company_id[0])

        if select_report in self.query_dictionary.keys():
            query = self.query_dictionary[select_report]
            full_query = query.format(start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT),
                                      where_customer_ids, where_branch_ids, where_company_id,
                                      where_group_id)
            self._cr.execute(full_query)
            result = self._cr.fetchall()
            data = {
                'result': result,
                'star_date': start_date,
                'end_date': end_date
            }
            return self.env.ref(select_report).report_action(
                self, data=data)
        else:
            data = {
                'model': select_report,
                'ids': self.ids,
                'form': {
                    'date_start': start_date, 'date_end': end_date, 'company_id': company_id[0],
                    'branch_ids': self.branch_ids,
                    'customer_ids': self.customer_ids,

                },
            }
            return self.env.ref(select_report).report_action(
                self, data=data)

    def get_excel_report(self):
        data = self.read()[0]
        where_customer_ids = "1=1"
        where_branch_ids = "1=1"
        where_company_id = "1=1"
        where_group_id = '1=1'
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        branch_ids = data.get('branch_ids')
        customer = data.get('customer_ids')
        company_id = data.get('company_id')
        select_report = data.get('select_cheque_report')
        if branch_ids:
            where_branch_ids = " ap.branch_id in %s" % str(tuple(branch_ids)).replace(',)', ')')
        if customer:
            where_customer_ids = " ap.partner_id in %s" % str(tuple(customer)).replace(',)', ')')

        if company_id and select_report != 'accounting_report.branchwise_report':
            where_company_id = " rb.company_id = {}".format(company_id[0])
        else:
            where_company_id = " aj.company_id = {}".format(company_id[0])

        if select_report in self.query_dictionary.keys():
            query = self.query_dictionary[select_report]
            full_query = query.format(start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT),
                                      where_customer_ids, where_branch_ids, where_company_id,
                                      where_group_id)
            self._cr.execute(full_query)
            result = self._cr.fetchall()
            data = {
                'result': result,
                'star_date': start_date,
                'end_date': end_date
            }

        if select_report == 'accounting_report.in_hand_report':
            self.make_check_in_hand_report(data=data)

    select_cheque_report = fields.Selection(cheque_report_list, string='Select Cheque Report')
    start_date = fields.Date(string="Start Date", default=datetime.now())
    end_date = fields.Date(string='End Date', default=datetime.now())
    customer_ids = fields.Many2many('res.partner', string='Customer')

    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),
                                 default=lambda self: self.env.user.company_id, required=True)

    branch_ids = fields.Many2many('res.branch', string='Branch')
