from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, datetime, relativedelta


class CollectionStatementReportWizard(models.TransientModel):
    _name = 'accounting.sale.gross.profit.report.wizard'

    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Date', required=True, default=fields.Date.today)
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),
                                 default=lambda self: self.env.user.company_id, required=True)
    # branch_ids = fields.Many2one('res.branch', string='Branch')
    branch_ids = fields.Many2many('res.branch', 'branchwise_report_sale_gross_profit_rel',
                                  'branchwise_report_sale_gross_profit_id',
                                  'branch_id', 'Branches')
    product_ids = fields.Many2many('product.product', string='Products')
    categ_ids = fields.Many2many('product.category', string='Categories')
    group_ids = fields.Many2many('product.group', string='Group')
    brand_ids = fields.Many2many('product.brand', string='Brand')
    model_ids = fields.Many2many('product.model', string='Model')
    partner_type = fields.Many2many('res.partner.category', 'partner_and_report_gross_rel', string='Customer Tag')
    partner_ids = fields.Many2many('res.partner', string='Customer', )

    @api.onchange('partner_type')
    def partner_ids_domain_set(self):
        if self.partner_type:
            return {'domain': {'partner_ids': [('category_id', 'in', self.partner_type)]}}
        return

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
                'product_ids': self.product_ids.ids,
                'categ_ids': self.categ_ids.ids,
                'group_ids': self.group_ids.ids,
                'brand_ids': self.brand_ids.ids,
                'model_ids': self.model_ids.ids,
                'partner_ids': self.partner_ids.ids,
                'partner_tags': self.partner_type.ids,
                # 'branch_name': self.branch_ids.name,
            },
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('accounting_report.account_sale_gross_profit_report').report_action(
            self, data=data)

    def excel_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.date_start, 'date_end': self.date_end, 'company_id': self.company_id.id,
                'branch_id': self.branch_ids,
                'product_ids': self.product_ids.ids,
                'categ_ids': self.categ_ids.ids,
                'group_ids': self.group_ids.ids,
                'brand_ids': self.brand_ids.ids,
                'model_ids': self.model_ids.ids,
                'partner_ids': self.partner_ids.ids,
                'partner_tags': self.partner_type.ids,
                # 'branch_name': self.branch_ids.name,
            },
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('accounting_report.account_sale_gross_profit_report_xls').report_action(
            self, data=data)


class CollectionStatementReportView(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.accounting_report.sale_gross_profit_view'

    @api.model
    def _get_report_values(self, docids, data=None):
        print(self)
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        branch_id = data['form']['branch_id']
        company_id = data['form']['company_id']
        product_ids = data['form']['product_ids']
        categ_ids = data['form']['categ_ids']
        group_ids = data['form']['group_ids']
        brand_ids = data['form']['brand_ids']
        model_ids = data['form']['model_ids']
        partner_ids = data['form']['partner_ids']
        partner_tags = data['form']['partner_tags']

        where_group_ids = " 1=1 "
        where_brand_ids = " 1=1 "
        where_model_ids = " 1=1 "
        where_product_ids = " 1=1 "
        where_categ_ids = " 1=1 "
        where_customr_ids = " 1=1 "
        where_customr_tags = " 1=1 "

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
        if product_ids:
            where_product_ids = " product_id in %s" % str(tuple(product_ids)).replace(',)', ')')
        if categ_ids:
            where_categ_ids = " categ_id in %s" % str(tuple(categ_ids)).replace(',)', ')')
        if group_ids:
            where_group_ids = " group_id in %s" % str(tuple(group_ids)).replace(',)', ')')
        if brand_ids:
            where_brand_ids = " brand_id in %s" % str(tuple(brand_ids)).replace(',)', ')')
        if model_ids:
            where_model_ids = " product_model_id in %s" % str(tuple(model_ids)).replace(',)', ')')
        if partner_ids:
            where_customr_ids = " partner_id in %s" % str(tuple(partner_ids)).replace(',)', ')')
        # if partner_tags:
        #     where_customr_tags = " rp.category_id in %s" % str(tuple(partner_tags)).replace(',)', ')')

        view_refresh = """REFRESH MATERIALIZED VIEW mvw_sales_gross_profit_details"""
        self._cr.execute(query=view_refresh)

        # final_query = """select br_name,invoice_date,invoice_id,invoice_no,COALESCE(sum(bill_amount),0),COALESCE(sum(cost_amount),0)
        #                 ,COALESCE(sum(bill_amount),0)-COALESCE(sum(cost_amount),0) as sales_profit from mvw_sales_gross_profit
        #                  where {} and {} and invoice_date between '{}' and '{}' group
        #                  by 1,2,3,4 order by 2""".format(company_id, where_branch_id,
        #                                                  start_date.strftime(DATETIME_FORMAT),
        #                                                  end_date.strftime(DATETIME_FORMAT))

        final_query = """select br_name,invoice_date,invoice_id,invoice_no,COALESCE(sum(bill_amount),0),COALESCE(sum(cost_amount),0)
 ,COALESCE(sum(bill_amount),0)-COALESCE(sum(cost_amount),0) as sales_profit from mvw_sales_gross_profit_details as mvw
 where {} and {}
 and {} and {} and {} and {} and {} and {} and {}
 and invoice_date between '{}' and '{}' group by 1,2,3,4 order by br_name""".format(company_id, where_branch_id,
                                                                              where_categ_ids, where_group_ids,
                                                                              where_brand_ids, where_model_ids,
                                                                              where_product_ids, where_customr_ids,
                                                                              where_customr_tags,
                                                                              start_date.strftime(
                                                                                  DATETIME_FORMAT),
                                                                              end_date.strftime(
                                                                                  DATETIME_FORMAT))

        self._cr.execute(query=final_query)
        query_result = self._cr.fetchall()
        profit_statement = dict()
        for res in query_result:
            if res[0] in profit_statement.keys():
                profit_statement[res[0]].append(res)
            else:
                profit_statement[res[0]] = list()
                profit_statement[res[0]].append(res)

        print(profit_statement)

        return {
            'date_start': date_start,
            'date_end': date_end,
            # 'branch': branch_name,
            'stock_gross_profit': profit_statement,
            'username': self.env.user.name,

        }
