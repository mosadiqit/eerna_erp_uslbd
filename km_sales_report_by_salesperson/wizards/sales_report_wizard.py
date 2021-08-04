from odoo import models, fields, api, _

class SalesReportBySalesperson(models.TransientModel):
    _name = 'sale.salesperson.report'

    start_date = fields.Datetime(string="Start Date", required=True)
    end_date = fields.Datetime(string="End Date", required=True)
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),
                                 default=lambda self: self.env.user.company_id,required=True)
    salesperson_ids = fields.Many2many('res.users', string="Salesperson", required=True)

    def _get_companies(self):
        query = """select * from res_company_users_rel where user_id={}""".format(self.env.user.id)
        self._cr.execute(query=query)
        allowed_companies = self._cr.fetchall()
        allowed_company = []
        for company in allowed_companies:
            allowed_company.append(company[0])
        return [('id', 'in', allowed_company)]

    # @api.onchange('company_id')
    # def get_sales_person(self):
    #     query="""select id from res_users where company_id={}""".format(self.company_id.id)
    #     self._cr.execute(query=query)
    #     sales_persons=self._cr.fetchall()
    #     self.salesperson_ids=[(6,0,sales_persons)]

    def print_sale_report_by_salesperson(self):
        print(self.company_id)
        sales_order = self.env['sale.order'].search([])
        sale_order_groupby_dict = {}
        for salesperson in self.salesperson_ids:
            filtered_sale_order = list(filter(lambda x: x.user_id == salesperson, sales_order))
            print('filtered_sale_order ===',filtered_sale_order)
            filtered_by_date = list(filter(lambda x: x.date_order >= self.start_date and x.date_order <= self.end_date, filtered_sale_order))
            filtered_by_company=list(filter(lambda x: x.company_id==self.company_id.id, filtered_by_date))
            sale_order_groupby_dict[salesperson.name] = filtered_by_company
            # sale_order_groupby_dict[salesperson.name] = filtered_by_date

        final_dist = {}
        for salesperson in sale_order_groupby_dict.keys():
            sale_data = []
            for order in sale_order_groupby_dict[salesperson]:
                temp_data = []
                temp_data.append(order.name)
                temp_data.append(order.date_order)
                temp_data.append(order.partner_id.name)
                temp_data.append(order.amount_total)
                sale_data.append(temp_data)
            final_dist[salesperson] = sale_data
        datas = {
            'ids': self,
            'model': 'sale.salesperson.report',
            'form': final_dist,
            'start_date': self.start_date,
            'end_date': self.end_date
        }
        return self.env.ref('km_sales_report_by_salesperson.action_report_by_salesperson').report_action([], data=datas)