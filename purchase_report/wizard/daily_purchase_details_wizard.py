import json
from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, BytesIO, xlsxwriter, base64
from custom_module.accounting_report.models.usl_xlxs_report_tools import UslXlxsReportUtil as utill


class DailyPurchaseDetailsWizard(models.TransientModel):
    _name = 'daily.purchase.details.report.wizard'

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Date', required=True, default=fields.Date.today)
    branch_id = fields.Many2one('res.branch', string='Branch')
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),
                                 default=lambda self: self.env.user.company_id, required=True)

    def _get_companies(self):
        query = """select * from res_company_users_rel where user_id={}""".format(self.env.user.id)
        self._cr.execute(query=query)
        allowed_companies = self._cr.fetchall()
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
                'branch_id': self.branch_id.id
            },
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('purchase_report.daily_purchase_details_report').report_action(
            self, data=data)

    def get_xlsx_report(self):
        User = self.env['res.users']
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.date_start, 'date_end': self.date_end, 'company_id': self.company_id.id,
                'branch_id': self.branch_id.id
            },
        }

        start_date = data['form']['date_start']
        end_date = data['form']['date_end']
        branch_id = data['form']['branch_id']
        company_id = data['form']['company_id']
        # branch_name = data['form']['branch_name']
        group_value = []

        # start_date = datetime.strptime(date_start, DATE_FORMAT)
        # end_date = datetime.strptime(date_end, DATE_FORMAT)
        delta = timedelta(days=1)
        if branch_id:
            where_branch_id = " po.branch_id = %s" % branch_id

        else:
            where_branch_id = " po.branch_id = %s" % User.browse(self.env.uid).branch_id.id

        if company_id:
            where_company_id = " acm.company_id = %s" % company_id

        else:
            where_company_id = "1=1"

        products = []
        query = """ select 
                    po.Date_Order
                    ,acm.name as invoice_no
                    ,pol.name as product_name
                    ,pol.product_uom_qty as quantity
                    ,pol.price_unit as unit_price
                    ,pol.price_subtotal as total_price_without_tax
                    ,pol.price_tax as tax
                    ,pol.price_total as total_price_with_tax
                    ,br.name as branch_name
                    ,pa.name as customer_name
                    ,acm.id as invoice_id
                    from purchase_Order as po
                    left join purchase_Order_line as pol on pol.Order_id=po.id
                    left join account_move as acm on acm.invoice_origin=po.name
                    left join res_branch as br on br.id=po.branch_id
                    left join res_partner as pa on pa.id=po.partner_id
                    where po.Date_Order::date  between '{}' and '{}'
                    and po.invoice_status='{}'
                    and acm.type='{}' and {} and {} """.format(start_date.strftime(DATETIME_FORMAT),
                                                               end_date.strftime(DATETIME_FORMAT), "invoiced",
                                                               "in_invoice", where_branch_id, where_company_id)

        self._cr.execute(query=query)
        query_results = self._cr.fetchall()
        # print(query_results)
        products_dic = dict()
        for query_result in query_results:
            list_key = tuple([query_result[0], query_result[1], query_result[8], query_result[9]])
            if list_key not in products_dic.keys():
                products_dic[list_key] = list()
                products_dic[list_key].append(query_result)
            else:
                products_dic[list_key].append(query_result)
        print(products_dic.keys())
        report_name = 'Daily Purchase Report'
        filename = '%s' % (report_name)
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = utill.add_workbook_format(workbook=workbook)

        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:I3', report_name, wbf['title_doc'])

        columns_group = [
            ('Date', 50, 'char', 'char'),
            ('Invoice No', 50, 'char', 'char'),
            ('Branch', 50, 'char', 'no'),
            ('Customer', 50, 'char', 'char'),

        ]
        cloumn_product = [
            ('Product Name', 50, 'char', 'no'),
            ('Qty', 50, 'float', 'float'),
            ('Unit Price', 50, 'float', 'float'),
            ('Total Price without Tax', 50, 'float', 'float'),
            ('TAX', 50, 'float', 'float'),
            ('Total Price with Tax', 50, 'float', 'float'),

        ]
        row = 6
        col = 0
        row = 6
        grand_total = 0
        for product in products_dic.keys():
            col = 0
            # print(product)

            sub_total = 0
            for index, column in enumerate(product, start=0):
                column_name = str(columns_group[index][0]) + " : " + str(column)
                column_width = columns_group[index][1]
                worksheet.set_column(col, col, column_width)
                worksheet.write(row - 1, col, column_name, wbf['header_orange'])
                col += 1
            row += 1
            col = 0
            for index, column in enumerate(cloumn_product, start=0):
                column_name = str(cloumn_product[index][0])
                column_width = cloumn_product[index][1]
                worksheet.set_column(col, col, column_width)
                worksheet.write(row - 1, col, column_name, wbf['header_orange'])
                col += 1
            row += 1

            for line in products_dic[product]:
                col = 0
                # print(line)

                for index, column in enumerate(line, start=2):
                    if index > 7:
                        break
                    else:
                        column_name = str(line[index])
                        worksheet.write(row - 1, col, column_name)
                        col += 1
                row += 1
                grand_total += line[7]
                sub_total += line[7]
            worksheet.merge_range('A%s:E%s' % (row, row), 'Sub Total', wbf['total_orange'])
            worksheet.write(row - 1, 5, sub_total, wbf['header_orange'])
            row += 2
        worksheet.merge_range('A%s:E%s' % (row, row), 'Grand Total', wbf['total_orange'])
        worksheet.write(row - 1, 5, grand_total, wbf['header_orange'])

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


class ReportDailyPurchaseDetailsReportView(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.purchase_report.daily_purchase_details_report_view'

    # @api.model
    # def _get_report_values(self, docids, data=None):
    #     date_start = data['form']['date_start']
    #     date_end = data['form']['date_end']
    #     branch_id=data['form']['branch_id']

    def _get_report_values(self, docids, data=None):
        User = self.env['res.users']
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        branch_id = data['form']['branch_id']
        company_id = data['form']['company_id']
        # branch_name = data['form']['branch_name']
        group_value = []

        start_date = datetime.strptime(date_start, DATE_FORMAT)
        end_date = datetime.strptime(date_end, DATE_FORMAT)
        delta = timedelta(days=1)
        if branch_id:
            where_branch_id = " po.branch_id = %s" % branch_id

        else:
            where_branch_id = " po.branch_id = %s" % User.browse(self.env.uid).branch_id.id

        if company_id:
            where_company_id = " acm.company_id = %s" % company_id

        else:
            where_company_id = "1=1"
        query1 = """select 
        po.date_Order
        ,acm.id as invoice_id
        ,acm.name as invoice_no
        ,br.name as branch_name
        ,pa.name as customer_name
        ,sum(po.amount_total) as total
        from Purchase_Order as po
        left join account_move as acm on acm.invoice_origin=po.name
        left join res_branch as br on br.id=po.branch_id
        left join res_partner as pa on pa.id=po.partner_id

        where po.date_Order::date  between '{}' and '{}'
            and po.invoice_status='{}'
            and acm.type='{}' and {} and {} group by po.date_Order
        ,acm.name
        ,br.name 
        ,pa.name
        ,acm.id""".format(start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT), "invoiced",
                          "in_invoice", where_branch_id, where_company_id)
        self._cr.execute(query=query1)
        query_result1 = self._cr.fetchall()

        for res in query_result1:
            group_value.append(res)

        docs = []
        products = []
        query = """ select 
            po.Date_Order
            ,acm.name as invoice_no
            ,pol.name as product_name
            ,pol.product_uom_qty as quantity
            ,pol.price_unit as unit_price
            ,pol.price_subtotal as total_price_without_tax
            ,pol.price_tax as tax
            ,pol.price_total as total_price_with_tax
            ,br.name as branch_name
            ,pa.name as customer_name
            ,acm.id as invoice_id
            from purchase_Order as po
            left join purchase_Order_line as pol on pol.Order_id=po.id
            left join account_move as acm on acm.invoice_origin=po.name
            left join res_branch as br on br.id=po.branch_id
            left join res_partner as pa on pa.id=po.partner_id
            where po.Date_Order::date  between '{}' and '{}'
            and po.invoice_status='{}'
            and acm.type='{}' and {} and {} """.format(start_date.strftime(DATETIME_FORMAT),
                                                       end_date.strftime(DATETIME_FORMAT), "invoiced", "in_invoice",
                                                       where_branch_id, where_company_id)

        self._cr.execute(query=query)
        query_result = self._cr.fetchall()

        for res in query_result:
            products.append(res)

        filtered_by_date_branch = list()

        total_orders = len(filtered_by_date_branch)
        # amount_total = sum(order.amount_total for order in filtered_by_date_branch)
        allsale = []
        allsale = filtered_by_date_branch
        print(allsale)

        docs.append({
            'date': start_date.strftime("%Y-%m-%d"),
            'total_orders': total_orders,
            # 'amount_total': amount_total,
            'company': self.env.user.company_id,

        })

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': start_date,
            'date_end': end_date,
            'group_value': group_value,
            'products': products,
            # 'docs': docs,

            # 'collection_statements': collection_statements
            # 'grand_amount_total': amount_total,

        }
