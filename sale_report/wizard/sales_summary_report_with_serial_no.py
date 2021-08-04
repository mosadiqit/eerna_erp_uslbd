import json
from datetime import datetime, timedelta

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, BytesIO, xlsxwriter, base64
import xlsxwriter
import base64
from odoo import fields, models, api
from io import BytesIO
from datetime import datetime


class SalesSummaryReportSn(models.TransientModel):
    _name = 'sales.summary.serial'
    _description = 'Find and print sales details with product serial no and buyer information'

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    date_start = fields.Date(string="Start Date", default=datetime.now())
    date_end = fields.Date(string="End Date",default=datetime.now())
    product_ids = fields.Many2many('product.product', 'sale_report_detail_product_rel_serial', 'sale_report_detail_id_serial',
                                   'product_id', 'Products')
    categ_ids = fields.Many2many('product.category', 'sale_report_detail_categ_rel_serial', 'sale_report_detail_id_serial',
                                 'categ_id', 'Categories')
    group_ids = fields.Many2many('product.group', 'sale_report_detail_group_rel_serial', 'sale_report_detail_id_serial',
                                 'group_id', 'Group')
    brand_ids = fields.Many2many('product.brand', 'sale_report_detail_brand_rel_serial', 'sale_report_detail_id_serial',
                                 'brand_id', 'Brand')
    model_ids = fields.Many2many('product.model', 'sale_report_detail_model_rel_serial', 'sale_report_detail_id_serial',
                                 'model_id', 'Model')
    location_ids = fields.Many2many('res.branch', 'ms_report_branch_rel_serial', 'sale_report_detail_id_serial',
                                    'branch_id', 'Branch')
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),
                                 default=lambda self: self.env.user.company_id, required=True)

    customer = fields.Many2many('res.partner','partner_sale_report_serial', string="Select Buyer")
    invoice_no = fields.Many2many('account.move','sale_report_serial',string="Invoice No")
    branch_ids = fields.Many2many('res.branch', string='Branch')



    @api.onchange('date_end','customer','invoice_no','date_start') # onchange function,show 'customer','invoice_id' in between 'date_end' and 'date_start'
    def get_invoice(self):
        print("Method called")
        for rec in self:
            if rec.date_start and rec.date_end and rec.customer:
                # print(rec.customer.id) # 'domain' is the 'key' of data dictionary
                return {'domain': {'invoice_no': [('invoice_date','>=',rec.date_start),('invoice_date','<=',rec.date_end),('partner_id','in',rec.customer.ids),('type','=','out_invoice')]}}
            return {'domain': {'invoice_no': [('invoice_date', '>=', rec.date_start), ('invoice_date', '<=', rec.date_end),('type','=','out_invoice')]}}

    def _get_companies(self):
        print("Company")
        query="""select * from res_company_users_rel where user_id={}""".format(self.env.user.id)
        self._cr.execute(query=query)
        allowed_companies=self._cr.fetchall()
        allowed_company=[]
        for company in allowed_companies:
            allowed_company.append(company[0])
        return [('id', 'in', allowed_company)]

    def print_report(self):
        data = self.read()[0]
        product_ids = data['product_ids']
        # print(product_ids)
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.date_start, 'date_end': self.date_end,'customer':self.customer,'product_ids':self.product_ids, 'invoice_no':self.invoice_no,'company_id': self.company_id.id,'branch_ids':self.branch_ids,
                'group_ids': self.group_ids,
            },
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('sale_report.sales_details_report_serial_no').with_context(landscape=True).report_action(
            self, data=data)
        # for rec in self:
        #     if rec.start_date and rec.end_date and rec.customer and rec.invoice_no:
        #         docs_origin = self.env['account.move'].search([''])
        #         docs = self.env['account.move'].search([('id','in',rec.invoice_no.ids)])
        #         print(docs)
        #     elif rec.start_date and rec.end_date and rec.invoice_no:
        #         docs = self.env['account.move'].search(
        #             [('invoice_date', '>=', rec.start_date), ('invoice_date', '<=', rec.end_date),('id','in',rec.invoice_no.ids)])
        #         print(docs)
        #     elif rec.start_date and rec.end_date:
        #         docs = self.env['account.move'].search([('invoice_date','>=',rec.start_date),('invoice_date','<=',rec.end_date)])
        #         print(docs)

    def print_excel_report(self):
        data = self.read()[0]
        product_ids = data['product_ids']
        # print(product_ids)
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.date_start, 'date_end': self.date_end, 'customer': self.customer,
                'product_ids': self.product_ids, 'invoice_no': self.invoice_no, 'company_id': self.company_id.id,'branch_ids':self.branch_ids, 'group_ids': self.group_ids,
            },
        }

        start_date = data['form']['date_start']
        end_date = data['form']['date_end']

        # branch_id = data['form']['branch_id']
        company_id = data['form']['company_id']
        customer_ids = data['form']['customer']
        product_ids = data['form']['product_ids']
        invoice_ids = data['form']['invoice_no']
        branch_ids = data['form']['branch_ids']
        print('branch ids excel',branch_ids)
        group_ids = data['form']['group_ids']
        print('date difference is',(end_date - start_date).days)

        where_product_ids = "1=1"
        where_customer_ids = "1=1"
        where_invoice_ids = "1=1"
        where_branch_ids = "1=1"
        where_group_ids = "1=1"

        # if product_ids and product_id != ():
        #     where_product_ids = " aml.product_id in {}".format(product_id)
        # if customer_ids and customer_id != ():
        #     where_customer_ids = " am.partner_id in {}".format(customer_id)
        # if invoice_ids and invoice_id != ():
        #     where_invoice_ids = " am.id in {}".format(invoice_id)

        get_product_ids = []
        print('first proudct ids',product_ids)
        if product_ids:
            where_product_ids = " aml.product_id in %s" % str(tuple(product_ids.ids)).replace(',)', ')')  # by using ids it returns tuple of all id
        #     for id in product_ids:
        #         if id != "":
        #             get_product_ids.append(int(id))  # take all 'product_ids' because in 'product_ids' stores all obj
        # if len(get_product_ids) == 1:
        #     where_product_ids = "aml.product_id = {}".format(get_product_ids[0]) # if length is 1 then take first element only
        # if len(get_product_ids) > 1:
        #     where_product_ids = "aml.product_id in {}".format(tuple(get_product_ids)) # if length is greater than 1 then create a tuple
        print('second where product ids',where_product_ids)

        get_customer_ids = []
        if customer_ids:
            where_customer_ids = "am.partner_id in %s" % str(tuple(customer_ids.ids)).replace(',)', ')') #'use 'customer_ids.ids' because take res.partner ids,if we don't use 'ids' then it sends objects
        print('where customer ids', where_customer_ids)
        if invoice_ids:
            where_invoice_ids = "am.id in %s" % str(tuple(invoice_ids.ids)).replace(',)', ')')
        print('where_invoice_ids', where_invoice_ids)
        # product_id = eval(product_ids.strip('product.product'))
        print('the ultimate branch ids is',branch_ids)
        print('the type of res.branch',type(branch_ids))
        branch_ids = str(branch_ids)
        branch_id = eval(branch_ids.strip('res.branch'))
        print('branch id initial', branch_id)
        if branch_id != ():
            branch_id = list(branch_id)
            branch_id.append(0)
            branch_id = tuple(branch_id)

        group_ids = str(group_ids)
        group_id = eval(group_ids.strip('product.group'))
        if group_id != ():
            group_id = list(group_id)
            group_id.append(0)
            group_id = tuple(group_id)

        if branch_ids and branch_id != ():
            where_branch_ids = " am.branch_id in {}".format(branch_id)
        if group_ids and group_id != ():
            where_group_ids = "pt.group_id in {}".format(group_id)



        # if product_id != ():
        #     product_id = list(product_id)
        #     product_id.append(0)
        #     product_id = tuple(product_id)
        #
        # customer_id = eval(customer_ids.strip('res.partner'))
        # if customer_id != ():
        #     customer_id = list(customer_id)
        #     customer_id.append(0)
        #     customer_id = tuple(customer_id)
        # # customer_id[-1]=0
        # print(customer_id)
        #
        # invoice_id = eval(invoice_ids.strip('account.move'))
        # if invoice_id != ():
        #     invoice_id = list(invoice_id)
        #     invoice_id.append(0)
        #     invoice_id = tuple(invoice_id)
        # branch_name = data['form']['branch_name']
        group_value = []

        # start_date = datetime.strptime(date_start, DATE_FORMAT)
        # end_date = datetime.strptime(date_end, DATE_FORMAT)
        # delta = timedelta(days=1)

        query = """
                        select distinct am.name as invoice_no,rs.name as buyer, pt.name, aml.quantity,aml.price_unit, aml.price_total, rb.name as branch,
                        pg.name as group,
                        (select string_agg(spl.name,',') 		
                        from stock_picking sp 
                        left join stock_move sm on sm.reference=sp.name 
                        left join stock_move_line sml on sml.move_id=sm.id  and sml.product_id = aml.product_id
                        left join stock_production_lot spl on spl.id=sml.lot_id where sp.origin = am.invoice_origin)
                        as serial_number
                        from account_move am 
                        left join res_branch as rb on am.branch_id = rb.id
                        left join res_partner rs on rs.id = am.partner_id
                        inner join account_move_line aml on am.id = aml.move_id
                        left join product_product pp on pp.id = aml.product_id
                        left join product_template pt on pt.id=pp.product_tmpl_id
                        left join product_group pg on pt.group_id = pg.id 
                        inner join account_account aa on aml.account_id = aa.id
                        where   am.invoice_date::DATE between '{}' and '{}' and {} and {} and {} and {} and {}
                         and  am.type = '{}' and am.state='{}' and aml.product_id > 0 and aa.internal_group = '{}'
                """.format(start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT), where_product_ids,
                           where_customer_ids, where_invoice_ids, where_branch_ids, where_group_ids, "out_invoice",
                           "posted", "income")
        print(query)
        print(query)
        self._cr.execute(query=query)
        query_result = self._cr.dictfetchall()
        final_list = list()
        print(query_result)
        # print(type(query_result[2]['serial_number']))
        # for res in query_result:
        #     group_value.append(res)
        for list_c in query_result:
            val = {
                'invoice': list_c['invoice_no'],
                'buyer': list_c['buyer'],
                'product': list_c['name'],
                'serial': str(list_c['serial_number']).split(','),
                'quantity': list_c['quantity'],
                'price': list_c['price_unit'],
                'total': list_c['price_total'],
                'branch': list_c['branch'],
                'group': list_c['group'],
            }
            final_list.append(val)
        print(final_list)
        invoice_dict = dict()

        for result in final_list:
            if result['invoice'] not in invoice_dict.keys():
                invoice_dict[result['invoice']] = list()
                invoice_dict[result['invoice']].append(result)
            else:
                invoice_dict[result['invoice']].append(result)
        print(invoice_dict)

        report_name = 'Sale Report With Serial Number'
        filename = '%s' % (report_name)
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)
        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:I3', report_name, wbf['title_doc'])
        invoice_group = [
            ('Invoice No.',30,'char','no'),
        ]
        column_product = [
            ('Buyer',30,'no','no'),
            ('Product',70,'char','char'),
            ('Quantity',13,'float','float'),
            ('Price',16,'float','float'),
            ('Total',17,'float','float'),
            ('Branch',16,'char','char'),
            ('Group',15,'char','char'),
        ]
        row = 4
        # col =0
        grand_total = 0
        # for column in columns:
        #     column_name = column[0]
        #     column_width = column[1]
        #     column_type = column[2]
        #     worksheet.set_column(col,col,column_width)
        #     worksheet.write(row-1, col, column_name, wbf['header_orange'])
        #     col += 1
        # row += 1
        # col1 = 0
        for coll in invoice_dict.keys():
            col = 0
            column_name = invoice_group[0][0]
            column_width = invoice_group[0][1]
            worksheet.set_column(col, col, column_width)
            worksheet.write(row-1, col, column_name, wbf['header_orange'])
            col += 1

            worksheet.write(row-1, col, coll,wbf['header_orange'])
            col += 1
            col2 =0
            row += 1
            for product in column_product: # for product header purpose
                column_name1 = product[0]
                column_width1 = product[1]
                column_type = product[2]
                worksheet.set_column(col2,col2,column_width1)
                worksheet.write(row-1,col2,column_name1,wbf['header_orange'])
                col2 += 1
            row += 1
            am = 0
            for item in invoice_dict[coll]:
                col3 = 0
                worksheet.write(row-1,col3,item['buyer'])
                col3 += 1
                worksheet.write(row - 1, col3, item['product'])
                col3 += 1
                worksheet.write(row - 1, col3, item['quantity'])
                col3 += 1
                worksheet.write(row - 1, col3, item['price'])
                col3 += 1
                worksheet.write(row - 1, col3, item['total'])
                col3 += 1
                worksheet.write(row - 1, col3, item['branch'])
                col3 += 1
                worksheet.write(row-1, col3, item['group'])
                row += 1
                am += item['total']
            row += 1
            worksheet.merge_range('A%s:D%s' % (row-1,row-1), 'Sub Total',wbf['total_orange'])

            # worksheet.write(row - 1, 3, 'Sub Total:', wbf['header_orange'])
            worksheet.write(row - 2, 4, am, wbf['header_orange'])
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


class SalesSummaryReportSerial(models.AbstractModel):
    _name = 'report.sale_report.sales_details_serial_report_view'

    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        # branch_id = data['form']['branch_id']
        company_id = data['form']['company_id']
        customer_ids = data['form']['customer']
        product_ids = data['form']['product_ids']
        invoice_ids = data['form']['invoice_no']
        branch_ids = data['form']['branch_ids']
        group_ids = data['form']['group_ids']
        print("branch ids pdf",branch_ids)
        print("first group ids",group_ids)

        product_id = eval(product_ids.strip('product.product'))
        if product_id != ():
            product_id = list(product_id)
            product_id.append(0)
            product_id = tuple(product_id)

        customer_id = eval(customer_ids.strip('res.partner'))
        if customer_id != ():
            customer_id = list(customer_id)
            customer_id.append(0)
            customer_id = tuple(customer_id)
        # customer_id[-1]=0
        print(customer_id)
        print('first invoice id',invoice_ids)

        invoice_id = eval(invoice_ids.strip('account.move'))
        print('invoice id',invoice_id)
        if invoice_id != ():
            invoice_id = list(invoice_id)
            invoice_id.append(0)
            invoice_id = tuple(invoice_id)
        print('last invoice id',invoice_id)
        # branch_name = data['form']['branch_name']
        group_value=[]

        # branch_id = eval(branch_ids.strip('account.move'))
        branch_id = eval(branch_ids.strip('res.branch'))
        print('the type of res.branch', type(branch_ids))
        print('branch id now now', branch_id)
        if branch_id != ():
            branch_id = list(branch_id)
            print('branch id second',branch_id)
            branch_id.append(0)
            print('branch id third',branch_id)
            branch_id = tuple(branch_id)
            print('branch id fourth',branch_id)

        group_id = eval(group_ids.strip('product.group'))
        print('group id initial',group_id)
        if group_id != ():
            group_id = list(group_id)
            print('group id is',group_id)
            group_id.append(0)
            print('group id second',group_id)
            group_id = tuple(group_id)
            print('group id fourth',group_id)

        start_date = datetime.strptime(date_start, DATE_FORMAT)
        end_date = datetime.strptime(date_end, DATE_FORMAT)
        delta = timedelta(days=1)
        where_product_ids =  "1=1"
        where_customer_ids = "1=1"
        where_invoice_ids = "1=1"
        where_branch_ids = "1=1"
        where_group_ids = "1=1"

        if product_ids and product_id != ():
            where_product_ids = " aml.product_id in {}".format(product_id)
        if customer_ids and customer_id != ():
            where_customer_ids = " am.partner_id in {}".format(customer_id)
        if invoice_ids and invoice_id != ():
            where_invoice_ids = " am.id in {}".format(invoice_id)
        if branch_ids and branch_id != ():
            where_branch_ids = " am.branch_id in {}".format(branch_id)
        if group_ids and group_id != ():
            where_group_ids = "pt.group_id in {}".format(group_id)

        print('where_invoice_ids',where_invoice_ids)
        print('where group ids', where_group_ids)

        # if branch_ids:
        #     where_branch_ids = " am.branch_id.id in %s" % str(tuple(branch_ids)).replace(',)', ')')
        # print('branch_ids',branch_ids)
        print('where branch ids',where_branch_ids)

        query = """
                select distinct am.name as invoice_no,rs.name as buyer, pt.name, aml.quantity,aml.price_unit, aml.price_total, rb.name as branch,
                pg.name as group,
                (select string_agg(spl.name,',') 		
                from stock_picking sp 
                left join stock_move sm on sm.reference=sp.name 
                left join stock_move_line sml on sml.move_id=sm.id  and sml.product_id = aml.product_id
                left join stock_production_lot spl on spl.id=sml.lot_id where sp.origin = am.invoice_origin)
                as serial_number
                from account_move am 
                left join res_branch as rb on am.branch_id = rb.id
                left join res_partner rs on rs.id = am.partner_id
                inner join account_move_line aml on am.id = aml.move_id
                left join product_product pp on pp.id = aml.product_id
                left join product_template pt on pt.id=pp.product_tmpl_id
                left join product_group pg on pt.group_id = pg.id 
                inner join account_account aa on aml.account_id = aa.id
                where   am.invoice_date::DATE between '{}' and '{}' and {} and {} and {} and {} and {}
                 and  am.type = '{}' and am.state='{}' and aml.product_id > 0 and aa.internal_group = '{}'
        """.format(start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT),where_product_ids,where_customer_ids,where_invoice_ids,where_branch_ids,where_group_ids,"out_invoice","posted","income")
        print(query)
        self._cr.execute(query=query)
        query_result = self._cr.dictfetchall()
        final_list = list()
        print(query_result)
        # print(type(query_result[2]['serial_number']))
        # for res in query_result:
        #     group_value.append(res)
        for list_c in query_result:
            val = {
                'invoice':list_c['invoice_no'],
                'buyer':list_c['buyer'],
                'product':list_c['name'],
                'serial':str(list_c['serial_number']).split(','), # create a list in key value in dictionary for serial number
                'quantity':list_c['quantity'],
                'price':list_c['price_unit'],
                'total':list_c['price_total'],
                'branch': list_c['branch'],
                'group': list_c['group'],
            }
            final_list.append(val)
        print(final_list)
        invoice_dict = dict()

        for result in final_list:
            if result['invoice'] not in invoice_dict.keys():
                invoice_dict[result['invoice']] = list()
                invoice_dict[result['invoice']].append(result)
            else:
                invoice_dict[result['invoice']].append(result)
        print('invoice dict is',invoice_dict)
        return {
            'date_start': start_date,
            'date_end': end_date,
            'data': invoice_dict,
        }





