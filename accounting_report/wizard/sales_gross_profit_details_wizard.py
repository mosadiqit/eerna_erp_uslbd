from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, datetime, relativedelta


class CollectionStatementReportWizard(models.TransientModel):
    _name = 'accounting.sale.gross.profit.details.report.wizard'

    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Date', required=True, default=fields.Date.today)
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),
                                 default=lambda self: self.env.user.company_id, required=True)
    # branch_ids = fields.Many2one('res.branch', string='Branch')
    branch_ids = fields.Many2many('res.branch', 'branchwise_report_sale_gross_profit_details_rel',
                                  'branchwise_report_sale_gross_profit_details_id',
                                  'branch_id', 'Branches')
    is_negetive_margin = fields.Boolean(string='Neg. Margin')

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
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.date_start, 'date_end': self.date_end, 'company_id': self.company_id.id,
                'branch_id': self.branch_ids,
                'negetive': self.is_negetive_margin
                # 'branch_name': self.branch_ids.name,
            },
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('accounting_report.account_sale_gross_profit_details_report').report_action(
            self, data=data)

    def get_excel_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.date_start, 'date_end': self.date_end, 'company_id': self.company_id.id,
                'branch_id': self.branch_ids,
                'negetive': self.is_negetive_margin
                # 'branch_name': self.branch_ids.name,
            },
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('accounting_report.account_sale_gross_profit_details_report_xls').report_action(
            self, data=data)


class CollectionStatementReportView(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.accounting_report.sale_gross_profit_details_view'

    @api.model
    def _get_report_values(self, docids, data=None):
        print(self)
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        branch_id = data['form']['branch_id']
        company_id = data['form']['company_id']
        neg = data['form']['negetive']

        new_branch_id = []
        x = branch_id.split("(")
        y = x[1].split(")")
        z = y[0].split(",")
        if z[0] != '':

            new_branch_id = [int(x) for x in z if x != '']
        else:
            where_branch_id = "1=1"

        if company_id:
            company_id = " c_id = %s" % company_id

        else:
            company_id = "1=1"
        # branch_name = data['form']['branch_name']

        start_date = datetime.strptime(date_start, DATE_FORMAT)
        end_date = datetime.strptime(date_end, DATE_FORMAT)
        date = (end_date + relativedelta(days=+ 1))

        if new_branch_id:
            if len(new_branch_id) == 1:
                where_branch_id = " br_id =%s" % new_branch_id[0]
            else:
                # where_branch_id ="br_id=%s"%branch_id
                where_branch_id = " br_id in %s" % str(tuple(new_branch_id))

        view_refresh = """REFRESH MATERIALIZED VIEW mvw_sales_gross_profit_details"""
        self._cr.execute(query=view_refresh)

        final_query = """select br_name,invoice_date,invoice_id,invoice_no,product_name,quantity,COALESCE(sum(bill_amount),0),COALESCE(sum(cost_amount),0)
                        ,COALESCE(sum(bill_amount),0)-COALESCE(sum(cost_amount),0) as sales_profit,(COALESCE(sum(bill_amount),0)-COALESCE(sum(cost_amount),0))*100/case when COALESCE(sum(cost_amount),0)=0 then 1 else COALESCE(sum(cost_amount),0) end as profit_margin from mvw_sales_gross_profit_details 
                         where {} and {} and invoice_date between '{}' and '{}' group
                         by 1,2,3,4,5,6 order by br_name""".format(company_id, where_branch_id,
                                                             start_date.strftime(DATETIME_FORMAT),
                                                             end_date.strftime(DATETIME_FORMAT))
        neq_query = """select * from (select br_name,invoice_date,invoice_id,invoice_no,product_name,quantity,COALESCE(sum(bill_amount),0),COALESCE(sum(cost_amount),0)
                        ,COALESCE(sum(bill_amount),0)-COALESCE(sum(cost_amount),0) as sales_profit,(COALESCE(sum(bill_amount),0)-COALESCE(sum(cost_amount),0))*100/case when COALESCE(sum(cost_amount),0)=0 then 1 else COALESCE(sum(cost_amount),0) end as profit_margin from mvw_sales_gross_profit_details 
                         where {} and {}  and invoice_date between '{}' and '{}' group
                         by 1,2,3,4,5,6 order by 2) as nnm where profit_margin <0""".format(company_id, where_branch_id,
                                                             start_date.strftime(DATETIME_FORMAT),
                                                             end_date.strftime(DATETIME_FORMAT))
        if neg:
            self._cr.execute(query=neq_query)
        else:
            self._cr.execute(query=final_query)
        query_result = self._cr.fetchall()
        profit_statement = dict()
        # for res in query_result:
        #     if res[0] in profit_statement.keys():
        #         profit_statement[res[0]].append(res)
        #     else:
        #         profit_statement[res[0]]=list()
        #         profit_statement[res[0]].append(res)
        for res in query_result:
            if res[0] not in profit_statement.keys():
                profit_statement[res[0]] = dict()
            if res[3] in profit_statement[res[0]].keys():
                profit_statement[res[0]][res[3]].append(res)
            else:
                profit_statement[res[0]][res[3]] = list()
                profit_statement[res[0]][res[3]].append(res)

        print(profit_statement)

        return {
            'date_start': date_start,
            'date_end': date_end,
            # 'branch': branch_name,
            'stock_gross_profit': profit_statement,
            'username': self.env.user.name,

        }
