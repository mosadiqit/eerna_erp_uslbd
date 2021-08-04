import json
import xlsxwriter
import base64
from odoo import fields, models, api
from io import BytesIO
from datetime import datetime
from pytz import timezone
import pytz
from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class SalesDetailsAnalysisWizard(models.TransientModel):
    _name = 'sales.details.analysis.report.wizard'

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Date', required=True, default=fields.Date.today)
    group_id = fields.Many2one('product.group', string='Group')
    brand_id = fields.Many2one('product.brand', string='Brand')
    product_id = fields.Many2one('product.template', string='Product')
    branch_id = fields.Many2one('res.branch', string='Branch', required="1")


    def get_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.date_start, 'date_end': self.date_end,
                'group_id': self.group_id.id, 'brand_id': self.brand_id.id,
                'product_id': self.product_id.id, 'branch_id': self.branch_id.id
            },
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('sale_report.sales_details_analysis_report').report_action(
            self, data=data)

    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone(self.env.user.tz or 'UTC'))

    def print_excel_report(self):
        data = self.read()[0]
        date_start = data['date_start']
        date_end = data['date_end']
        group_id = data['group_id'][0]
        brand_id = data['brand_id'][0]
        product_id = data['product_id'][0]
        branch_id = data['branch_id'][0]

        start_date = datetime.strptime(str(date_start), DATE_FORMAT)
        end_date = datetime.strptime(str(date_end), DATE_FORMAT)

        datetime_string = self.get_default_date_model().strftime("%Y-%m-%d %H:%M:%S")
        date_string = self.get_default_date_model().strftime("%Y-%m-%d")
        report_name = 'Sales Details Report'
        filename = '%s %s' % (report_name, date_string)

        columns = [
            ('Branch Name', 50, 'char', 'char'),
            ('S.Person', 30, 'char', 'char'),
            ('Sales Order No', 20, 'char', 'char'),
            ('Invoice No', 30, 'char', 'char'),
            ('Remarks', 30, 'char', 'char'),
            ('Buyer Name', 30, 'char', 'char'),
            ('Brand', 30, 'char', 'char'),
            ('Group', 30, 'char', 'char'),
            ('Product Name', 30, 'char', 'char'),
            ('Qty', 30, 'float', 'char'),
            ('Unit Price', 20, 'float', 'char'),
            ('Total Value', 20, 'float', 'char'),
            ('Inv.Date', 20, 'datetime', 'datetime'),
            ('S.O Date', 20, 'datetime', 'datetime'),
            ]

        datetime_format = '%Y-%m-%d %H:%M:%S'
        utc = datetime.now().strftime(datetime_format)
        utc = datetime.strptime(utc, datetime_format)
        tz = self.get_default_date_model().strftime(datetime_format)
        tz = datetime.strptime(tz, datetime_format)
        duration = tz - utc
        hours = duration.seconds / 60 / 60
        if hours > 1 or hours < 1:
            hours = str(hours) + ' hours'
        else:
            hours = str(hours) + ' hour'

        query = """ select 
              br.name as branch_name
              ,pas.name as sales_person
              ,so.name as sales_order_no
              ,acm.name as invoice_no
              ,acm.narration as remarks
              ,pa.name as customer_name
              ,pb.name as brand_name
              ,pg.name as group_name
              ,sol.name as product_name
              ,sol.product_uom_qty as quantity
              ,sol.price_unit as unit_price
              ,sol.price_subtotal as total_price_without_tax
              ,sol.price_tax as tax
              ,sol.price_total as total_price_with_tax
              ,acm.date as Invoice_date
              ,so.Date_Order
              from Sale_Order as so
              left join Sale_Order_line as sol on sol.Order_id=so.id
              left join account_move as acm on acm.invoice_origin=so.name
              left join res_branch as br on br.id=so.branch_id
              left join res_partner as pa on pa.id=so.partner_id
              left join res_partner as pas on pas.id=so.create_uid
              left join product_product pp on pp.id=sol.product_id
              left join product_template pt on pt.id=pp.product_tmpl_id
              left join product_group pg on pg.id=pt.group_id
              left join product_brand pb on pb.id=pt.brand_id
              left join product_model pm on pm.id=pt.product_model_id
              where so.Date_Order::date  between '{}' and '{}'
        and so.invoice_status='{}'
        and acm.type='{}' 
        and pg.id='{}'
        and pb.id='{}'
        and pt.id='{}'
        and so.branch_id={} """.format(start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT), "invoiced", "out_invoice", group_id, brand_id, product_id, branch_id)

        self._cr.execute(query)
        result = self._cr.fetchall()

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)

        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:I3', report_name, wbf['title_doc'])

        row = 5

        col = 0
        for column in columns:
            column_name = column[0]
            column_width = column[1]
            column_type = column[2]
            worksheet.set_column(col, col, column_width)
            worksheet.write(row - 1, col, column_name, wbf['header_orange'])

            col += 1

        row += 1
        row1 = row
        no = 1

        column_float_number = {}
        for res in result:
            col = 0
            for column in columns:
                column_name = column[0]
                column_width = column[1]
                column_type = column[2]
                if column_type == 'char':
                    col_value = res[col - 1] if res[col - 1] else ''
                    wbf_value = wbf['content']
                elif column_type == 'no':
                    col_value = no
                    wbf_value = wbf['content']
                elif column_type == 'datetime':
                    col_value = res[col - 1].strftime('%Y-%m-%d %H:%M:%S') if res[col - 1] else ''
                    wbf_value = wbf['content']
                else:
                    col_value = res[col - 1] if res[col - 1] else 0
                    if column_type == 'float':
                        wbf_value = wbf['content_float']
                    else:  # number
                        wbf_value = wbf['content_number']
                    column_float_number[col] = column_float_number.get(col, 0) + col_value

                worksheet.write(row - 1, col, col_value, wbf_value)

                col += 1

            row += 1
            no += 1

        worksheet.merge_range('A%s:B%s' % (row, row), 'Grand Total', wbf['total_orange'])
        for x in range(len(columns)):
            if x in (0, 1):
                continue
            column_type = columns[x][3]
            if column_type == 'char':
                worksheet.write(row - 1, x, '', wbf['total_orange'])
            else:
                if column_type == 'float':
                    wbf_value = wbf['total_float_orange']
                else:  # number
                    wbf_value = wbf['total_number_orange']
                if x in column_float_number:
                    worksheet.write(row - 1, x, column_float_number[x], wbf_value)
                else:
                    worksheet.write(row - 1, x, 0, wbf_value)

        worksheet.write('A%s' % (row + 2), 'Date %s (%s)' % (datetime_string, self.env.user.tz or 'UTC'),
                        wbf['content_datetime'])
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


class ReportSalesDetailsAnalysisReportView(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.sale_report.sales_details_analysis_report_view'


    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        group_id = data['form']['group_id']
        brand_id = data['form']['brand_id']
        product_id = data['form']['product_id']
        branch_id = data['form']['branch_id']
        # branch_name = data['form']['branch_name']

        start_date = datetime.strptime(date_start, DATE_FORMAT)
        end_date = datetime.strptime(date_end, DATE_FORMAT)
        delta = timedelta(days=1)

        docs = []
        products=[]
        query=""" select 
        br.name as branch_name
        ,pas.name as sales_person
        ,so.name as sales_order_no
        ,acm.name as invoice_no
        ,acm.narration as remarks
        ,pa.name as customer_name
        ,pb.name as brand_name
        ,pg.name as group_name
        ,sol.name as product_name
        ,sol.product_uom_qty as quantity
        ,sol.price_unit as unit_price
        ,sol.price_subtotal as total_price_without_tax
        ,sol.price_tax as tax
        ,sol.price_total as total_price_with_tax
        ,acm.date as Invoice_date
        ,so.Date_Order
        from Sale_Order as so
        left join Sale_Order_line as sol on sol.Order_id=so.id
        left join account_move as acm on acm.invoice_origin=so.name
        left join res_branch as br on br.id=so.branch_id
        left join res_partner as pa on pa.id=so.partner_id
        left join res_partner as pas on pas.id=so.create_uid
        left join product_template pt on pt.id=product_id
        left join product_group pg on pg.id=pt.group_id
        left join product_brand pb on pb.id=pt.brand_id
        left join product_model pm on pm.id=pt.product_model_id
        where so.Date_Order::date  between '{}' and '{}'
        and so.invoice_status='{}'
        and acm.type='{}' 
        and pg.id='{}'
        and pb.id='{}'
        and pt.id='{}'
         and so.branch_id={} """.format(start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT), "invoiced", "out_invoice", group_id, brand_id, product_id, branch_id)

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
            'products': products,


        }







