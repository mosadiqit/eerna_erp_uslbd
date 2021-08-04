import json
from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, BytesIO, xlsxwriter, relativedelta, base64


class DailySalesDetailsWizard(models.TransientModel):
    _name = 'daily.sales.details.report.wizard'

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

    def print_excel(self):
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
        company_id = data['form']['company_id']
        branch_id = data['form']['branch_id']
        print("data", data)
        print("start_date", start_date)
        print("end_date", end_date)
        print("company_id", company_id)
        print("branch_id", branch_id)

        # branch_name = data['form']['branch_name']
        group_value = []

        date = (end_date + relativedelta(days=+ 1))
        delta = timedelta(days=1)
        if branch_id:
            where_branch_id = " so.branch_id = %s" % branch_id

        else:
            where_branch_id = "1=1"

        if company_id:
            where_company_id = " acm.company_id = %s" % company_id

        else:
            where_company_id = "1=1"

        query1 = """select 
                        so.Date_Order
                        ,acm.id as invoice_id
                        ,acm.name as invoice_no
                        ,br.name as branch_name
                        ,pa.name as customer_name
                        ,sum(aml.price_total) as total
                        from Sale_Order as so
                        left join account_move as acm on acm.invoice_origin=so.name
                        left join account_move_line aml on acm.id = aml.move_id
                        left join res_branch as br on br.id=so.branch_id
                        left join res_partner as pa on pa.id=so.partner_id

                        where acm.type = 'out_invoice' and acm.state = 'posted' and acm.invoice_date::date  between '{}' and '{}'
                            and account_root_id=52048
                            and acm.type='{}' and {} and {} group by so.Date_Order
                        ,acm.name
                        ,br.name 
                        ,pa.name
                        ,acm.id""".format(start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT),
                                          "out_invoice", where_branch_id, where_company_id)
        self._cr.execute(query=query1)
        query_result1 = self._cr.fetchall()
        print("q1",query_result1)
        group_dic = dict()
        for q_result in query_result1:
            list_key = tuple([q_result[3], q_result[0], q_result[2], q_result[4],q_result[1]])
            if list_key not in group_dic.keys():
                group_dic[list_key] = list()
                group_dic[list_key].append(q_result)
            else:
                group_dic[list_key].append(q_result)

        for res in query_result1:
            group_value.append(res)

        docs = []
        products = []


        filtered_by_date_branch = list()

        total_orders = len(filtered_by_date_branch)
        # amount_total = sum(order.amount_total for order in filtered_by_date_branch)
        allsale = []
        allsale = filtered_by_date_branch

        docs.append({
            'date': start_date.strftime("%Y-%m-%d"),
            'total_orders': total_orders,
            # 'amount_total': amount_total,
            'company': self.env.user.company_id,

        })

        report_name = 'Daily Sales Details Report'
        filename = '%s' % (report_name)
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)
        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:D3', report_name, wbf['title_doc'])

        columns_group = [
            ('Branch', 30, 'char', 'no'),
            ('Date', 30, 'char', 'char'),
            ('Invoice No', 30, 'char', 'char'),
            ('Customer', 50, 'char', 'char'),
        ]
        cloumn_product = [
            ('Product Name', 50, 'char', 'no'),
            ('Qty', 10, 'float', 'float'),
            ('Unit Price', 20, 'float', 'float'),
            ('TAX', 10, 'float', 'float'),
            ('Value', 10, 'float', 'float'),
        ]

        row = 6

        row = 6
        grand_total = 0

        for group in group_dic.keys():
            col = 0
            # row +=1
            # print(product)
            # sub_total = 0
            # grand_total = 0
            for index, column in enumerate(group, start=0):
                # col=0
                if index > 3:
                    break
                else:
                    column_name = str(columns_group[index][0]) + " : " + str(column)
                    column_width = columns_group[index][1]
                    worksheet.set_column(col, col, column_width)
                    worksheet.write(row - 1, col, column_name, wbf['header_orange'])
                    col += 1
            row += 1


            col2 = 0
            # grand_total = 0
            for product in cloumn_product:
                # col2=0
                column_name1 = product[0]
                column_width = product[1]
                column_type = product[2]
                worksheet.set_column(col, col, column_width)
                worksheet.write(row - 1, col2, column_name1, wbf['header_orange'])
                # worksheet.merge_range('A2:I3', column_name, wbf['header_orange'])
                col2 += 1
            # row += 1
            row += 1
            invoice_id = group[4]

            query = """ select distinct 
                                                        so.Date_Order
                                                        ,acm.name as invoice_no
                                                        ,sol.name as product_name
                                                        ,sol.product_uom_qty as quantity
                                                        ,sol.price_unit as unit_price
                                                        ,sol.price_subtotal as total_price_without_tax
                                                        ,sol.price_tax as tax
                                                        ,sol.price_total as total_price_with_tax
                                                        ,br.name as branch_name
                                                        ,pa.name as customer_name
                                                        ,acm.id as invoice_id
                                                        from Sale_Order as so
                                                        left join Sale_Order_line as sol on sol.Order_id=so.id
                                                        left join account_move as acm on acm.invoice_origin=so.name
                                                        left join account_move_line aml on acm.id = aml.move_id
                                                        left join res_branch as br on br.id=so.branch_id
                                                        left join res_partner as pa on pa.id=so.partner_id
                                                        where acm.type = 'out_invoice' and acm.state = 'posted' and acm.invoice_date::date  between '{}' and '{}'
                                                        and account_root_id=52048
                                                        and acm.type='{}' and {} and {}  """.format(
                start_date.strftime(DATETIME_FORMAT),
                end_date.strftime(DATETIME_FORMAT),
                "out_invoice",
                where_branch_id, where_company_id)

            self._cr.execute(query=query)
            query_result = self._cr.fetchall()
            # print("query_result", query_result)
            # for res in query_result:
            #     products.append(res)
            sub_total = 0
            for item in query_result:
                print("A")
                col3 = 0
                # print(len(query_result))

                if group[4] == item[10]:
                    print("item:",item)
                    print(group[4],item[10])
                    worksheet.write(row - 1, col3, item[2])
                    col3 += 1
                    worksheet.write(row - 1, col3, item[3])
                    col3 += 1
                    worksheet.write(row - 1, col3, item[4])
                    col3 += 1
                    worksheet.write(row - 1, col3, item[6])
                    col3 += 1
                    worksheet.write(row - 1, col3, item[7])
                    col3 += 1

                    row += 1
                    sub_total += item[7]
                    grand_total += item[7]
                    print("sub_total", sub_total)


                worksheet.write(row - 1, 3, 'Sub Total:', wbf['header_orange'])
                worksheet.write(row - 1, 4, sub_total, wbf['header_orange'])
                # row+=1
                # grand_total += item[7]
                print(grand_total)
                # row += 2
            row += 2
            print(grand_total)
            worksheet.write(row - 1, 3, 'Grand Total:', wbf['header_orange'])
            worksheet.write(row - 1, 4, grand_total, wbf['header_orange'])
        # worksheet.merge_range('A%s:D%s' % (row, row), 'Grand Total', wbf['total_orange'])
        # worksheet.write(row - 1, 4, grand_total, wbf['header_orange'])
        row +=1





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

    def add_workbook_format(self, workbook):
        colors = {
            'white_orange': '#FFFFDB',
            'orange': '#FFC300',
            'red': '#FF0000',
            'yellow': '#F6FA03',
        }

        wbf = {}
        wbf['header'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': '#FFFFDB', 'font_color': '#000000', 'font_name': 'Georgia'})
        wbf['header'].set_border()

        wbf['header_orange'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': colors['orange'], 'font_color': '#000000',
             'font_name': 'Georgia'})
        wbf['header_orange'].set_border()

        wbf['header_yellow'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': colors['yellow'], 'font_color': '#000000',
             'font_name': 'Georgia'})
        wbf['header_yellow'].set_border()

        wbf['header_no'] = workbook.add_format(
            {'bold': 1, 'align': 'center', 'bg_color': '#FFFFDB', 'font_color': '#000000', 'font_name': 'Georgia'})
        wbf['header_no'].set_border()
        wbf['header_no'].set_align('vcenter')

        wbf['footer'] = workbook.add_format({'align': 'left', 'font_name': 'Georgia'})

        wbf['content_datetime'] = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss', 'font_name': 'Georgia'})
        wbf['content_datetime'].set_left()
        wbf['content_datetime'].set_right()

        wbf['content_date'] = workbook.add_format({'num_format': 'yyyy-mm-dd', 'font_name': 'Georgia'})
        wbf['content_date'].set_left()
        wbf['content_date'].set_right()

        wbf['title_doc'] = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 20,
            'font_name': 'Georgia',
        })

        wbf['company'] = workbook.add_format({'align': 'left', 'font_name': 'Georgia'})
        wbf['company'].set_font_size(11)

        wbf['content'] = workbook.add_format()
        wbf['content'].set_left()
        wbf['content'].set_right()

        wbf['content_float'] = workbook.add_format({'align': 'right', 'num_format': '#,##0.00', 'font_name': 'Georgia'})
        wbf['content_float'].set_right()
        wbf['content_float'].set_left()

        wbf['content_number'] = workbook.add_format({'align': 'right', 'num_format': '#,##0', 'font_name': 'Georgia'})
        wbf['content_number'].set_right()
        wbf['content_number'].set_left()

        wbf['content_percent'] = workbook.add_format({'align': 'right', 'num_format': '0.00%', 'font_name': 'Georgia'})
        wbf['content_percent'].set_right()
        wbf['content_percent'].set_left()

        wbf['total_float'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['white_orange'], 'align': 'right', 'num_format': '#,##0.00',
             'font_name': 'Georgia'})
        wbf['total_float'].set_top()
        wbf['total_float'].set_bottom()
        wbf['total_float'].set_left()
        wbf['total_float'].set_right()

        wbf['total_number'] = workbook.add_format(
            {'align': 'right', 'bg_color': colors['white_orange'], 'bold': 1, 'num_format': '#,##0',
             'font_name': 'Georgia'})
        wbf['total_number'].set_top()
        wbf['total_number'].set_bottom()
        wbf['total_number'].set_left()
        wbf['total_number'].set_right()

        wbf['total'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['white_orange'], 'align': 'center', 'font_name': 'Georgia'})
        wbf['total'].set_left()
        wbf['total'].set_right()
        wbf['total'].set_top()
        wbf['total'].set_bottom()

        wbf['total_float_yellow'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['yellow'], 'align': 'right', 'num_format': '#,##0.00',
             'font_name': 'Georgia'})
        wbf['total_float_yellow'].set_top()
        wbf['total_float_yellow'].set_bottom()
        wbf['total_float_yellow'].set_left()
        wbf['total_float_yellow'].set_right()

        wbf['total_number_yellow'] = workbook.add_format(
            {'align': 'right', 'bg_color': colors['yellow'], 'bold': 1, 'num_format': '#,##0', 'font_name': 'Georgia'})
        wbf['total_number_yellow'].set_top()
        wbf['total_number_yellow'].set_bottom()
        wbf['total_number_yellow'].set_left()
        wbf['total_number_yellow'].set_right()

        wbf['total_yellow'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['yellow'], 'align': 'center', 'font_name': 'Georgia'})
        wbf['total_yellow'].set_left()
        wbf['total_yellow'].set_right()
        wbf['total_yellow'].set_top()
        wbf['total_yellow'].set_bottom()

        wbf['total_float_orange'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['orange'], 'align': 'right', 'num_format': '#,##0.00',
             'font_name': 'Georgia'})
        wbf['total_float_orange'].set_top()
        wbf['total_float_orange'].set_bottom()
        wbf['total_float_orange'].set_left()
        wbf['total_float_orange'].set_right()

        wbf['total_number_orange'] = workbook.add_format(
            {'align': 'right', 'bg_color': colors['orange'], 'bold': 1, 'num_format': '#,##0', 'font_name': 'Georgia'})
        wbf['total_number_orange'].set_top()
        wbf['total_number_orange'].set_bottom()
        wbf['total_number_orange'].set_left()
        wbf['total_number_orange'].set_right()

        wbf['total_orange'] = workbook.add_format(
            {'bold': 1, 'bg_color': colors['orange'], 'align': 'center', 'font_name': 'Georgia'})
        wbf['total_orange'].set_left()
        wbf['total_orange'].set_right()
        wbf['total_orange'].set_top()
        wbf['total_orange'].set_bottom()

        wbf['header_detail_space'] = workbook.add_format({'font_name': 'Georgia'})
        wbf['header_detail_space'].set_left()
        wbf['header_detail_space'].set_right()
        wbf['header_detail_space'].set_top()
        wbf['header_detail_space'].set_bottom()

        wbf['header_detail'] = workbook.add_format({'bg_color': '#E0FFC2', 'font_name': 'Georgia'})
        wbf['header_detail'].set_left()
        wbf['header_detail'].set_right()
        wbf['header_detail'].set_top()
        wbf['header_detail'].set_bottom()

        return wbf, workbook

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
        return self.env.ref('sale_report.daily_sales_details_report').report_action(
            self, data=data)


class ReportDailySalesDetailsReportView(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.sale_report.daily_sales_details_report_view'

    # @api.model
    # def _get_report_values(self, docids, data=None):
    #     date_start = data['form']['date_start']
    #     date_end = data['form']['date_end']
    #     branch_id=data['form']['branch_id']

    def _get_report_values(self, docids, data=None):
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
            where_branch_id = " so.branch_id = %s" % branch_id

        else:
            where_branch_id = "1=1"

        if company_id:
            where_company_id = " acm.company_id = %s" % company_id

        else:
            where_company_id = "1=1"
        # query1 = """select
        # so.Date_Order
        # ,acm.id as invoice_id
        # ,acm.name as invoice_no
        # ,br.name as branch_name
        # ,pa.name as customer_name
        # ,sum(so.amount_total) as total
        # from Sale_Order as so
        # left join account_move as acm on acm.invoice_origin=so.name
        # left join res_branch as br on br.id=so.branch_id
        # left join res_partner as pa on pa.id=so.partner_id
        #
        # where so.Date_Order::date  between '{}' and '{}'
        #     and so.invoice_status='{}'
        #     and acm.type='{}' and {} and {} group by so.Date_Order
        # ,acm.name
        # ,br.name
        # ,pa.name
        # ,acm.id""".format(start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT), "invoiced",
        #                   "out_invoice", where_branch_id, where_company_id)

        query1 = """select 
                so.Date_Order
                ,acm.id as invoice_id
                ,acm.name as invoice_no
                ,br.name as branch_name
                ,pa.name as customer_name
                ,sum(aml.price_total) as total
                from Sale_Order as so
                left join account_move as acm on acm.invoice_origin=so.name
                left join account_move_line aml on acm.id = aml.move_id
                left join res_branch as br on br.id=so.branch_id
                left join res_partner as pa on pa.id=so.partner_id

                where acm.type = 'out_invoice' and acm.state = 'posted' and acm.invoice_date::date  between '{}' and '{}'
                    and account_root_id=52048
                    and acm.type='{}' and {} and {} group by so.Date_Order
                ,acm.name
                ,br.name 
                ,pa.name
                ,acm.id""".format(start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT),
                                  "out_invoice", where_branch_id, where_company_id)
        self._cr.execute(query=query1)
        query_result1 = self._cr.fetchall()
        print("Q1", query_result1)

        for res in query_result1:
            group_value.append(res)
        print("group_value", group_value)
        docs = []
        products = []

        query = """ select distinct 
                    so.Date_Order
                    ,acm.name as invoice_no
                    ,sol.name as product_name
                    ,sol.product_uom_qty as quantity
                    ,sol.price_unit as unit_price
                    ,sol.price_subtotal as total_price_without_tax
                    ,sol.price_tax as tax
                    ,sol.price_total as total_price_with_tax
                    ,br.name as branch_name
                    ,pa.name as customer_name
                    ,acm.id as invoice_id
                    from Sale_Order as so
                    left join Sale_Order_line as sol on sol.Order_id=so.id
                    left join account_move as acm on acm.invoice_origin=so.name
                    left join account_move_line aml on acm.id = aml.move_id
                    left join res_branch as br on br.id=so.branch_id
                    left join res_partner as pa on pa.id=so.partner_id
                    where acm.type = 'out_invoice' and acm.state = 'posted' and acm.invoice_date::date  between '{}' and '{}'
                    and account_root_id=52048
                    and acm.type='{}' and {} and {} """.format(start_date.strftime(DATETIME_FORMAT),
                                                               end_date.strftime(DATETIME_FORMAT),
                                                               "out_invoice",
                                                               where_branch_id, where_company_id)

        self._cr.execute(query=query)
        query_result = self._cr.fetchall()
        print("Q2", query_result)
        for res in query_result:
            products.append(res)

        filtered_by_date_branch = list()

        total_orders = len(filtered_by_date_branch)
        # amount_total = sum(order.amount_total for order in filtered_by_date_branch)
        allsale = []
        allsale = filtered_by_date_branch

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
