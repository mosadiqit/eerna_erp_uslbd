# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, BytesIO, xlsxwriter, base64


class SaleSummaryReportWizard(models.TransientModel):
    _name = 'sale.summary.report.wizard'

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Date', required=True, default=fields.Date.today)
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),default=lambda self: self.env.user.company_id,required=True)
    branch_ids = fields.Many2one('res.branch', string='Branch')

    def _get_companies(self):
        query="""select * from res_company_users_rel where user_id={}""".format(self.env.user.id)
        self._cr.execute(query=query)
        allowed_companies=self._cr.fetchall()
        allowed_company=[]
        for company in allowed_companies:
            allowed_company.append(company[0])
        return  [('id', 'in', allowed_company)]
    def print_excel_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.date_start, 'date_end': self.date_end, 'company_id': self.company_id.id,
                'branch_ids': self.branch_ids.id
            },
        }
        start_date = data['form']['date_start']
        end_date = data['form']['date_end']
        branch_id = data['form']['branch_ids']
        branch_name = self.env['res.branch'].search([
            ('id', 'in', [branch_id])
        ]).name
        company_id = data['form']['company_id']

        SO = self.env['account.move']
        # start_date = datetime.strptime(date_start, DATE_FORMAT)
        # end_date = datetime.strptime(date_end, DATE_FORMAT)
        delta = timedelta(days=1)

        docs = []
        print("docs", docs)
        # orders = SO.search([
        #     ('date', '>=', start_date.strftime(DATETIME_FORMAT)),
        #     ('date', '<=', end_date.strftime(DATETIME_FORMAT)),
        #     ('state', 'in', ['posted', 'draft'])
        # ])
        if company_id and branch_id:
            filtered_by_date = list(SO.search([
                ('date', '>=', start_date.strftime(DATETIME_FORMAT)),
                ('date', '<=', end_date.strftime(DATETIME_FORMAT)),
                ('state', 'in', ['posted', 'draft']),
                ('type', 'in', ['out_invoice']),
                ('branch_id', 'in', [branch_id]),
                ('company_id', 'in', [company_id])

            ]))
        elif company_id:
            filtered_by_date = list(SO.search([
                ('date', '>=', start_date.strftime(DATETIME_FORMAT)),
                ('date', '<=', end_date.strftime(DATETIME_FORMAT)),
                ('state', 'in', ['posted', 'draft']),
                ('type', 'in', ['out_invoice']),
                ('company_id', 'in', [company_id])
            ]))
        else:
            filtered_by_date = list(SO.search([
                ('date', '>=', start_date.strftime(DATETIME_FORMAT)),
                ('date', '<=', end_date.strftime(DATETIME_FORMAT)),
                ('state', 'in', ['posted', 'draft']),
                ('type', 'in', ['out_invoice'])

            ]))

        total_orders = len(filtered_by_date)
        amount_total = sum(order.amount_total for order in filtered_by_date)
        allsale = []
        allsale = filtered_by_date
        print("allsale", allsale)
        docs.append({
            'date': start_date.strftime("%Y-%m-%d"),
            'total_orders': total_orders,
            'amount_total': amount_total,
            'company': self.env.user.company_id,

        })
        report_name = 'Sales Summary Report'
        filename = '%s' % (report_name)
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)
        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:D3', report_name, wbf['title_doc'])

        columns_group = [
            ('Date ', 30, 'char', 'char'),
            ('Invoice No', 30, 'char', 'char'),
            ('Customer', 50, 'char', 'char'),
            ('Sales Person', 50, 'char', 'char'),
            ('Total Amount', 30, 'char', 'char'),
        ]

        col = 0
        row = 4

        for group in columns_group:
            # col=0
            column_name1 = group[0]
            column_width = group[1]
            column_type = group[2]
            worksheet.set_column(col, col, column_width)
            worksheet.write(row - 1, col, column_name1, wbf['header_orange'])
            # worksheet.merge_range('A2:I3', column_name, wbf['header_orange'])
            col += 1
            # row += 1
        row += 1
        # col1=0
        column_branch=[('Branch Name ', 30, 'char', 'char'),]
        for branch in column_branch:
            column_name = str(branch[0]) + " : " + str(branch_name) if branch_name else str(branch[0])
            column_width = branch[1]
            worksheet.set_column(col, col, column_width)
            worksheet.merge_range('A5:E5', column_name, wbf['header_orange'])
            # worksheet.write(row - 1, col, column_name, wbf['header_orange'])

            row += 1
        grand_total=0
        for doc in allsale:
            col1 = 0
            worksheet.write(row - 1, col1, doc.invoice_date)
            col1+=1
            worksheet.write(row - 1, col1, doc.name)
            col1 += 1
            worksheet.write(row - 1, col1, doc.partner_id.name)
            col1 += 1
            worksheet.write(row - 1, col1, doc.invoice_user_id.name)
            col1 += 1
            worksheet.write(row - 1, col1, doc.amount_total)
            # col1+=1
            row+=1
            grand_total += doc.amount_total
            print(doc)
        worksheet.write(row - 1, 3, 'Grand Total:', wbf['header_orange'])
        worksheet.write(row - 1, 4, grand_total, wbf['header_orange'])
        row+=1
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

        wbf['content_float'] = workbook.add_format(
            {'align': 'right', 'num_format': '#,##0.00', 'font_name': 'Georgia'})
        wbf['content_float'].set_right()
        wbf['content_float'].set_left()

        wbf['content_number'] = workbook.add_format(
            {'align': 'right', 'num_format': '#,##0', 'font_name': 'Georgia'})
        wbf['content_number'].set_right()
        wbf['content_number'].set_left()

        wbf['content_percent'] = workbook.add_format(
            {'align': 'right', 'num_format': '0.00%', 'font_name': 'Georgia'})
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
            {'align': 'right', 'bg_color': colors['yellow'], 'bold': 1, 'num_format': '#,##0',
             'font_name': 'Georgia'})
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
            {'align': 'right', 'bg_color': colors['orange'], 'bold': 1, 'num_format': '#,##0',
             'font_name': 'Georgia'})
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
                'date_start': self.date_start, 'date_end': self.date_end,'company_id':self.company_id.id,'branch_ids':self.branch_ids.id
            },
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('sale_report.sale_summary_report').report_action(
            self, data=data)


class ReportSaleSummaryReportView(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.sale_report.sale_summary_report_view'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        branch_id = data['form']['branch_ids']
        branch_name = self.env['res.branch'].search([
            ('id','in',[branch_id])
        ]).name
        company_id = data['form']['company_id']

        SO = self.env['account.move']
        start_date = datetime.strptime(date_start, DATE_FORMAT)
        end_date = datetime.strptime(date_end, DATE_FORMAT)
        delta = timedelta(days=1)

        docs = []
        print("docs", docs)
        # orders = SO.search([
        #     ('date', '>=', start_date.strftime(DATETIME_FORMAT)),
        #     ('date', '<=', end_date.strftime(DATETIME_FORMAT)),
        #     ('state', 'in', ['posted', 'draft'])
        # ])
        if company_id and branch_id:
            filtered_by_date = list(SO.search([
                    ('date', '>=', start_date.strftime(DATETIME_FORMAT)),
                    ('date', '<=', end_date.strftime(DATETIME_FORMAT)),
                    ('state', 'in', ['posted', 'draft']),
                    ('type', 'in', ['out_invoice']),
                    ('branch_id', 'in', [branch_id]),
                    ('company_id', 'in', [company_id])

                ]))
        elif company_id:
            filtered_by_date = list(SO.search([
                ('date', '>=', start_date.strftime(DATETIME_FORMAT)),
                ('date', '<=', end_date.strftime(DATETIME_FORMAT)),
                ('state', 'in', ['posted', 'draft']),
                ('type', 'in', ['out_invoice']),
                ('company_id', 'in', [company_id])
            ]))
        else:
            filtered_by_date = list(SO.search([
                ('date', '>=', start_date.strftime(DATETIME_FORMAT)),
                ('date', '<=', end_date.strftime(DATETIME_FORMAT)),
                ('state', 'in', ['posted', 'draft']),
                ('type', 'in', ['out_invoice'])

            ]))

        total_orders = len(filtered_by_date)
        amount_total = sum(order.amount_total for order in filtered_by_date)
        allsale =[]
        allsale = filtered_by_date
        print("allsale", allsale)
        docs.append({
            'date': start_date.strftime("%Y-%m-%d"),
            'total_orders': total_orders,
            'amount_total': amount_total,
            'company': self.env.user.company_id,

        })

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': start_date,
            'date_end': end_date,
            'branch_name': branch_name,
            'docs': docs,
            'allsale': allsale,
            'grand_amount_total': amount_total,

        }





