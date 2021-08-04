from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, datetime, relativedelta, BytesIO, xlsxwriter, \
    base64


class CollectionStatementReportWizard(models.TransientModel):
    _name = 'customer.bp.report.wizard'

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Date', required=True, default=fields.Date.today)
    customer_ids=fields.Many2many('res.partner','bp_report_customer_rel','bp_report_customer_id','part_id','Customer')
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
                'customer_ids': self.customer_ids,
                # 'branch_name': self.branch_ids.name,
            },
        }
        start_date = data['form']['date_start']
        end_date = data['form']['date_end']
        customer_ids = data['form']['customer_ids']
        company_id = data['form']['company_id']
        #
        new_customer_ids = []
        # x = customer_ids.split("(")
        # y = x[1].split(")")
        # z = y[0].split(",")
        where_customer_ids = "1=1"
        where_branch_ids = "1=1"
        where_branch_ids = "1=1"
        if customer_ids:
            where_customer_ids = "am.partner_id in %s" % str(tuple(customer_ids.ids)).replace(',)',
                                                                                      ')')  # create a tuple and remove comma

        # if len(new_customer_ids) == 1:
        #     where_branch_ids = "so.branch_id = {}".format(new_customer_ids[0])
        # if len(new_customer_ids) > 1:
        #     where_branch_ids = "so.branch_id in {}".format(tuple(new_customer_ids))


        if company_id:
            where_company_id = " am.company_id = %s" % company_id

        else:
            where_company_id = "1=1"

        # start_date = datetime.strptime(date_start, DATE_FORMAT)
        # end_date = datetime.strptime(date_end, DATE_FORMAT)

        query = """select am.invoice_date,rp.name,am.name,sum(price_unit) from account_move am
               left join account_move_line aml on aml.move_id=am.id
               left join res_partner rp on rp.id=am.partner_id
               where {} and am.type='out_invoice' and am.state='posted' and aml.name like '%BP%' and aml.price_unit>0 and am.invoice_date between '{}' and '{}' and  {} group by 1,2,3 """.format(
            where_customer_ids, start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT),
            where_company_id)
        self._cr.execute(query=query)
        result = self._cr.fetchall()
        print("result", result)
        customer_bp = dict()
        for res in result:
            invoice_date = str(res[0])
            if invoice_date not in customer_bp.keys():
                customer_bp[invoice_date] = dict()
            if res[1] in customer_bp[invoice_date].keys():
                customer_bp[invoice_date][res[1]].append(res)
            else:
                customer_bp[invoice_date][res[1]] = list()
                customer_bp[invoice_date][res[1]].append(res)

        print("cutomer bp", customer_bp)

        report_name = 'Customer BP Statement'
        filename = '%s' % (report_name)
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)
        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:D3', report_name, wbf['title_doc'])

        columns_group = [
            ('SL', 30, 'no', 'no'),
            ('Invoice No', 30, 'char', 'char'),
            ('BP Amount', 50, 'char', 'char'),
        ]

        col = 0
        row = 4

        for group in columns_group :
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
        # col1 = 0
        grand_total = 0
        for date_group in customer_bp.keys():
            worksheet.merge_range('A%s:C%s'%(row,row), str(date_group), wbf['header_orange'])
            row += 1
            # col1 = 0
            print("date_group:", date_group)

            for collection in customer_bp[date_group]:
                col1 = 0
                print("collection:",collection)
                worksheet.merge_range('A%s:C%s'%(row,row),collection, wbf['header_orange'])
                col1 += 1
                row += 1
                sl=1
                sub_total = 0
                for invoice in customer_bp[date_group][collection]:
                    col2=0
                    worksheet.write(row - 1,col2, sl)
                    sl += 1
                    col2+=1
                    worksheet.write(row-1,col2,invoice[2])
                    col2 += 1
                    worksheet.write(row-1,col2,invoice[3])
                    # col1 += 1
                    row += 1
                    sub_total += invoice[3]
                    grand_total += invoice[3]
                worksheet.write(row - 1, 1, 'Sub Total:', wbf['header_orange'])
                worksheet.write(row - 1, 2, sub_total, wbf['header_orange'])
                # grand_total += invoice[3]

                row+=2
            # row += 1
                # worksheet.write(row - 1, col1, collection[0], wbf['header_orange'])
                # col1 += 1
            worksheet.write(row - 1, 1, 'Grand Total:', wbf['header_orange'])
            worksheet.write(row - 1, 2, grand_total, wbf['header_orange'])
        row += 1
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
                'date_start': self.date_start, 'date_end': self.date_end,'company_id':self.company_id.id, 'customer_ids': self.customer_ids,
                # 'branch_name': self.branch_ids.name,
            },
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('custom_sale_invoice_report.custom_sale_customer_bp_report').report_action(
            self, data=data)

class  CustomerBPView(models.AbstractModel):
    _name = 'report.custom_sale_invoice_report.customer_bp_view'

    @api.model
    def _get_report_values(self, docids, data=None):
        print(docids)
        print(data['context']['allowed_company_ids'])
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        customer_ids = data['form']['customer_ids']
        company_id = data['form']['company_id']



        new_customer_ids = []
        x = customer_ids.split("(")
        y = x[1].split(")")
        z = y[0].split(",")
        if z[0] != '':

            new_customer_ids = [int(x) for x in z if x != '']

        else:
            where_customer_ids = "1=1"

        if new_customer_ids:
            if len(new_customer_ids) == 1:
                where_customer_ids = " am.partner_id =%s" % new_customer_ids[0]
            else:

                where_customer_ids = " am.partner_id in %s" % str(tuple(new_customer_ids))
        # if data['context']['allowed_company_ids']:
        #     if len(data['context']['allowed_company_ids']) ==1 :
        #         where_company_ids="am.company_id = %s"% data['context']['allowed_company_ids'][0]
        #     else:
        #         where_company_ids="am.company_id in %s"% str(tuple(data['context']['allowed_company_ids']))

        if company_id:
            where_company_id = " am.company_id = %s" % company_id

        else:
             where_company_id = "1=1"

        start_date = datetime.strptime(date_start, DATE_FORMAT)
        end_date = datetime.strptime(date_end, DATE_FORMAT)

        query="""select am.invoice_date,rp.name,am.name,sum(price_unit) from account_move am
        left join account_move_line aml on aml.move_id=am.id
        left join res_partner rp on rp.id=am.partner_id
        where {} and am.type='out_invoice' and am.state='posted' and aml.name like '%BP%' and aml.price_unit>0 and am.invoice_date between '{}' and '{}' and  {} group by 1,2,3 """.format(where_customer_ids,start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT),where_company_id)
        self._cr.execute(query=query)
        result=self._cr.fetchall()
        print("result",result)
        customer_bp=dict()
        for res in result:
            invoice_date=str(res[0])
            if invoice_date not in customer_bp.keys():
                customer_bp[invoice_date]=dict()
            if res[1] in customer_bp[invoice_date].keys():
                customer_bp[invoice_date][res[1]].append(res)
            else:
                customer_bp[invoice_date][res[1]]=list()
                customer_bp[invoice_date][res[1]].append(res)

        print("cutomer bp",customer_bp)
        return {
            'date_start': date_start,
            'date_end': date_end,
            # 'branch': branch_name,
            'customer_bp': customer_bp,
            'username': self.env.user.name,

        }