from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, datetime, relativedelta, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, BytesIO, xlsxwriter, base64
from odoo import fields, models
import xlsxwriter
import base64
from odoo import fields, models, api
from io import BytesIO
from datetime import datetime
from pytz import timezone
import pytz

# class InheritResBranch(models.Model):
#     _inherit = 'res.branch'
#     _order = 'name asc'


class SaleSummaryLocationWiseReportWizard(models.TransientModel):
    _name = 'sale.summary.location.wise.wizard'

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Date', required=True, default=fields.Date.today)
    # customer_ids=fields.Many2many('res.partner','bp_report_customer_rel','bp_report_customer_id','part_id','Customer')
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),
                                 default=lambda self: self.env.user.company_id, required=True)
    branch_ids=fields.Many2many('res.branch', 'location_wise_sale_summary_report__rel', 'location_wise_sale_summary_report_id',
                                    'branch_id', 'Branches')
    # branch_ids = fields.Many2many('stock.location', 'branchwise1_report_stock_location_rel',
    #                                 'branchwise1_report_stock_id',
    #                                 'location_id', 'Locations')

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
                'date_start': self.date_start, 'date_end': self.date_end,'company_id':self.company_id.id, 'branch_ids': self.branch_ids,
                # 'branch_name': self.branch_ids.name,
            },
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('sale_report.sale_summary_location_wise_report').report_action(
            self, data=data)

    def print_excel_report(self):
        # data = self.read()[0]
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.date_start, 'date_end': self.date_end, 'company_id': self.company_id.id,
                'branch_ids': self.branch_ids,
                # 'branch_name': self.branch_ids.name,
            },
        }
        start_date = data['form']['date_start']
        end_date = data['form']['date_end']
        branch_ids = data['form']['branch_ids']
        company_id = data['form']['company_id']
        # start_date = datetime.strptime(date_start, DATE_FORMAT)
        # end_date = datetime.strptime(date_end, DATE_FORMAT)
        print('branch_ids',branch_ids)

        # if branch_ids != '':
        #     branch_ids = branch_ids.split('(')
        #     branch_ids = branch_ids[1].split(')')
        #     branch_ids = branch_ids[0].split(',')
        #     get_branch_ids = []
        #
        #     for id in branch_ids:
        #         if id != "":
        #             get_branch_ids.append(int(id))
        #     print(get_branch_ids)
        #     print(company_id)

        get_branch_ids = []
        where_branch_ids = "1=1"
        if branch_ids:
            where_branch_ids = " so.branch_id in %s" % str(tuple(branch_ids)).replace(',)', ')') # create a tuple and remove comma
            for id in branch_ids:
                if id != "":
                    get_branch_ids.append(int(id))

        where_company_id = "1=1"

        if len(get_branch_ids) == 1:
            where_branch_ids = "so.branch_id = {}".format(get_branch_ids[0])
        if len(get_branch_ids) > 1:
            where_branch_ids = "so.branch_id in {}".format(tuple(get_branch_ids))
        if company_id:
            where_company_id = " am.company_id = %s" % company_id
        print('branch ids',branch_ids)
        print('branch ids.ids',branch_ids.ids)
        print('where_branch_ids',where_branch_ids)

        query = """select so.branch_id,rb.name,sum(so.amount_total) from sale_order so
                        left join res_branch rb on so.branch_id=rb.id
                        left join account_move am on am.invoice_origin=so.name where so.state='sale' 
                        and am.invoice_date::date between '{}' and '{}'   and {} and {} and  am.type='out_invoice' and am.state in {} 
                        group by so.branch_id,rb.name order by rb.name""".format(start_date.strftime(DATETIME_FORMAT),
                                                                                 end_date.strftime(DATETIME_FORMAT),
                                                                                 where_branch_ids, where_company_id,
                                                                                 ('posted', 'draft'))
        self._cr.execute(query=query)
        result = self._cr.fetchall()
        total = 0.0
        percentage_sum = 0.0
        sale_summary_location_wise_final_result = []
        for res in result:
            total += res[2]
        for res in result:
            percentage = round((res[2] / total) * 100, 2)
            # pre_percentage=round(res[2]/total,2)
            # percentage=round(pre_percentage*100,2)
            percentage_sum += percentage
            list_convertion = list(res)
            list_convertion.insert(3, percentage)
            sale_summary_location_wise_final_result.append(tuple(list_convertion))
        print(sale_summary_location_wise_final_result)
        percentage_sum = round(percentage_sum, 0)

        report_name = 'Sale Summary Location Wise Report'
        filename = '%s' % (report_name)

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)
        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:I3',report_name,wbf['title_doc'])
        columns_group = [
            ('SL',20,'char','no'),
            ('Location',40,'char','no'),
            ('Total Amount',30,'float','float'),
            ('Percentage',20,'float','float'),
        ]
        row = 5
        col = 0
        for column in columns_group:
            column_name = column[0]
            column_width = column[1]
            column_type = column[2]
            worksheet.set_column(col, col, column_width)
            worksheet.write(row - 1, col, column_name, wbf['header_orange'])
            col += 1
        row += 1
        sl = 1
        gt = 0
        percent = 0
        for sale in sale_summary_location_wise_final_result:
            col1 = 0
            worksheet.write(row-1,col1,sl)
            col1 += 1
            worksheet.write(row-1,col1,sale[1])
            col1 += 1
            worksheet.write(row-1,col1,sale[2])
            col1 += 1
            worksheet.write(row-1,col1,sale[3])
            col1 += 1
            gt += sale[2]
            percent += sale[3]

            sl += 1
            row += 1
        worksheet.write(row - 1, 1, 'Grand Total:',wbf['header_orange'])
        worksheet.write(row - 1, 2, gt,wbf['header_orange'])
        worksheet.write(row - 1, 3, percent,wbf['header_orange'])

        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'datas': out, 'datas_fname': filename}) # 'datas','datas_fname' is a field of same class
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


class ReportSaleSummaryLocationWiseReportView(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.sale_report.sale_summary_location_wise_report_view'

    def _get_report_values(self, docids, data=None):

        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        branch_ids = data['form']['branch_ids']
        company_id = data['form']['company_id']
        start_date = datetime.strptime(date_start, DATE_FORMAT)
        end_date = datetime.strptime(date_end, DATE_FORMAT)

        if branch_ids!='':
            branch_ids=branch_ids.split('(')
            branch_ids=branch_ids[1].split(')')
            branch_ids=branch_ids[0].split(',')
            get_branch_ids=[]

            for id in branch_ids:
                if id!="":
                    get_branch_ids.append(int(id))
            print(get_branch_ids)
            print(company_id)
        where_branch_ids="1=1"
        where_company_id = "1=1"
        if len(get_branch_ids) == 1:
            where_branch_ids = "so.branch_id = {}".format(get_branch_ids[0])
        if len(get_branch_ids)>1:
            where_branch_ids="so.branch_id in {}" .format(tuple(get_branch_ids))
        if company_id:
            where_company_id = " am.company_id = %s" % company_id

        query="""select so.branch_id,rb.name,sum(so.amount_total) from sale_order so
                left join res_branch rb on so.branch_id=rb.id
                left join account_move am on am.invoice_origin=so.name where so.state='sale' 
                and am.invoice_date::date between '{}' and '{}'   and {} and {} and  am.type='out_invoice' and am.state in {} 
                group by so.branch_id,rb.name order by rb.name""".format(start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT),where_branch_ids,where_company_id,('posted','draft'))
        self._cr.execute(query=query)
        result=self._cr.fetchall()
        total=0.0
        percentage_sum=0.0
        sale_summary_location_wise_final_result=[]
        for res in result:
            total+=res[2]
        for res in result:
            percentage=round((res[2]/total)*100,2)
            # pre_percentage=round(res[2]/total,2)
            # percentage=round(pre_percentage*100,2)
            percentage_sum+=percentage
            list_convertion=list(res)
            list_convertion.insert(3,percentage)
            sale_summary_location_wise_final_result.append(tuple(list_convertion))
        print(sale_summary_location_wise_final_result)
        percentage_sum=round(percentage_sum,0)
        print('sale summary location wise final result',sale_summary_location_wise_final_result)


        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': start_date,
            'date_end': end_date,
            # 'group_value':group_value,
            # 'products':products,
            'docs': self.env['account.move'].browse(docids),
            'sale_summary_location_wise_final_result': sale_summary_location_wise_final_result,
            'total':total,
            'percentage_sum':percentage_sum
            # 'grand_amount_total': amount_total,

        }
