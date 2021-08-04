# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, BytesIO, xlsxwriter, base64


class AgedCustomerReportWizard(models.TransientModel):
    _name = 'aged.customer.report.wizard'



    company_id = fields.Many2one('res.company', string='Company', domain=lambda self:self._get_companies(),default=lambda self: self.env.user.company_id,required=True)
    branch_ids = fields.Many2one( 'res.branch',string='Branch')
    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Date', required=True, default=fields.Date.today)


    def _get_companies(self):
        query="""select * from res_company_users_rel where user_id={}""".format(self.env.user.id)
        self._cr.execute(query=query)
        allowed_companies=self._cr.fetchall()
        allowed_company=[]
        for company in allowed_companies:
            allowed_company.append(company[0])
        return  [('id', 'in', allowed_company)]

    def get_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.date_start, 'date_end': self.date_end,'company_id':self.company_id.id, 'branch_id': self.branch_ids.id,
                'branch_name': self.branch_ids.name,
            },
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('sale_report.aged_customer_list_report').report_action(
            self, data=data)



class AreaWiseSalesReportView(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.sale_report.aged_customer_list_view'

    @api.model
    def _get_report_values(self, docids, data=None):

        branch_id = data['form']['branch_id']
        branch_name = data['form']['branch_name']
        company_id=data['form']['company_id']
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']

        # query = """select (cast(date_trunc('month',current_date) as date)) startdate"""
        # self._cr.execute(query=query)
        # result = self._cr.fetchall()
        # date_start = result[0]
        #
        # query = """select (cast(date_trunc('month',current_date)-INTERVAL '90 day' as date)) todate"""
        # self._cr.execute(query=query)
        # result_1 = self._cr.fetchall()
        # date_end = result_1[0]

        if branch_id:
            branch_id = " m.branch_id = %s" % branch_id

        else:
             branch_id = "1=1"

        if company_id:
            company_id = " m.company_id = %s" % company_id

        else:
             company_id = "1=1"

        query = """select distinct p.id,p.name,ca.area_name,max(m.date) as last_trans_date,sum(ml.debit) as debit,sum(ml.credit) as credit, (sum(debit)-sum(credit)) as Balance 
                from res_partner p
                left join account_move m on m.partner_id=p.id
                left join account_move_line ml on m.id=ml.move_id
                left join customer_area_setup ca on ca.id=p.customer_area
                where m.state='posted' --and 
                and p.id not in
                (select distinct m.partner_id from account_move_line ml
                left join account_move m on m.id=ml.move_id 
                where {} and m.date between '{}' and '{}' and {} and m.partner_id is not null) 
                group by p.id,p.name,ca.area_name
                order by p.name,ca.area_name
                """.format(branch_id, date_start, date_end, company_id)

        self._cr.execute(query=query)
        query_result = self._cr.fetchall()

        return {
            'date_start': date_start,
            'date_end': date_end,
            'branch': branch_name,
            'idle_customer': query_result,

        }
