from datetime import datetime, timedelta
from odoo import models, fields
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, BytesIO, xlsxwriter, base64
from odoo import fields, models
import xlsxwriter
import base64
from odoo import fields, models, api
from io import BytesIO
from datetime import datetime
from pytz import timezone
import pytz


class SaleReportBuyerWise(models.TransientModel):
    _name = "sale.buyerwise.report.wizard"
    _description = "Sale report buyer wise"
    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)

    def _get_companies(self):
        query = """select * from res_company_users_rel where user_id={}""".format(self.env.user.id)
        self._cr.execute(query=query)
        allowed_companies = self._cr.fetchall()
        allowed_company = []
        print(allowed_companies)
        for company in allowed_companies:
            allowed_company.append(company[0])
        return [('id', 'in', allowed_company)]

    def get_report(self):
        data = self.read()[0] # data takes a dictionary,where attribute has key value pair
        print("data is",data)

        location_ids = data['location_ids'] # data is read the 0th index file which is fetched,else we use 'form' in place of data fetch
        start_date = data['start_date']
        end_date = data['end_date']
        company_ids = data['company_id']
        # name = data['name']
        product_ids = data['product_ids']
        # print('product_ids',product_ids)
        customer = data['customer']
        group = data['group']

        # start_date = start_date.strftime('%Y-%M-%D')
        print(type(start_date), end_date)
        where_company_ids = "1=1"
        where_customer_ids = "1=1"
        where_branch_ids = "1=1"
        where_product_ids = "1=1"
        where_group = "1=1"
        where_customer = "1=1"


        # if location_ids:
        #     where_location_ids = " so.branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        # #     where_location_ids2 = " branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        # if group_ids:
        #     where_group_ids = " reg.group_id in %s" % str(tuple(group_ids)).replace(',)', ')')

        # if customer_ids:
        #     where_customer_ids = "rp.name = {}".format(customer_ids)
        #     print("where customer ids",where_customer_ids)

        # if name:
        #     where_customer_ids = " rp.name = %s" % name
        # print('product_ids_prev',product_ids)

        if product_ids:
            # where_product_ids = " ol.product_id in %s" % str(tuple(product_ids)).replace(',)', ')')
            where_product_ids = " aml.product_id in %s" % str(tuple(product_ids)).replace(',)', ')') # we don't need to use 'product_ids.ids' because of using 'data' read

        print('where_product_ids',where_product_ids)

        if group:
            where_group = " rpc.id in %s" % str(tuple(group)).replace(',)', ')')
            # where_supplier_wise_po = " rp.name = '%s'" % str(supplier_wise_po[1])
            print("Group", where_group)

        if customer:
            where_customer = " rp.id in %s" % str(tuple(customer)).replace(',)', ')')
            # where_supplier_wise_po = " rp.name = '%s'" % str(supplier_wise_po[1])
            print(where_customer)

        if location_ids:
            where_branch_ids = " am.branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        if company_ids:
            where_company_ids = " am.company_id = {}".format(company_ids[0])

        query = """
                      select rp.name as buyer,sum(aml.price_total) as total_amount, rpc.name as buyer_catogry,rb.id from account_move as am
                    inner join account_move_line aml on am.id = aml.move_id
                    left join res_partner as rp on am.partner_id=rp.id
                    left join res_branch rb on am.branch_id = rb.id
                    left join account_account aa on aml.account_id = aa.id
                    left join res_partner_res_partner_category_rel as rl on am.partner_id = rl.partner_id
                    left join res_partner_category rpc on rpc.id = rl.category_id
                    where am.type = 'out_invoice' and am.state = 'posted'
                    and {} and aa.internal_group = 'income' and am.invoice_date::DATE between '{}' and '{}'
                    and {} and {} and {} and {} and {}
                    group by rp.name,rpc.name,rb.id
                """.format(where_branch_ids, start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT),
                           where_customer_ids, where_company_ids,where_group,where_customer,where_product_ids)
        print(query)
        print('print pdf report')
        self._cr.execute(query)
        result = self._cr.fetchall()
        # result = []
        # for i in results:
        #     result.append(i)

        print('result is',result)
        data = {
            'result': result,
            'start_date': start_date,
            'end_date': end_date,
        }
        print('data is',data)
        return self.env.ref('sale_report.sale_buyerwise_report').report_action(
            self, data=data)

    start_date = fields.Date(string="Start Date", default=datetime.now())
    end_date = fields.Date(string='End Date', default=datetime.now())
    # name = fields.Many2many('res.partner', string='Customer')
    location_ids = fields.Many2many('res.branch', string='Branch')
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),
                                 default=lambda self: self.env.user.company_id, required=True)
    product_ids = fields.Many2many('product.product','sale_report_buyerwise_product_rel','sale_report_detail_buyerwise_id','product_id',string='Products')
    customer = fields.Many2many('res.partner', string='Customer')
    group = fields.Many2many('res.partner.category', string='Group')

    def print_excel_report(self):
        data = self.read()[0]
        print("data is", data)

        location_ids = data[
            'location_ids']  # data is read the 0th index file which is fetched,else we use 'form' in place of data fetch
        start_date = data['start_date']
        end_date = data['end_date']
        company_ids = data['company_id']
        # name = data['name']
        product_ids = data['product_ids']
        print('product_ids now',product_ids)
        customer = data['customer']
        group = data['group']

        # start_date = start_date.strftime('%Y-%M-%D')
        print(type(start_date), end_date)
        where_company_ids = "1=1"
        where_customer_ids = "1=1"
        where_branch_ids = "1=1"
        where_product_ids = "1=1"
        where_group = "1=1"
        where_customer = "1=1"

        if product_ids:
            # where_product_ids = " ol.product_id in %s" % str(tuple(product_ids)).replace(',)', ')')
            where_product_ids = " aml.product_id in %s" % str(tuple(product_ids)).replace(',)', ')') # data returns a dictionary,for that reason we don't need to use 'product_ids.ids' for returning a tuple

        print('where_product_ids', where_product_ids)

        if group:
            where_group = " rpc.id in %s" % str(tuple(group)).replace(',)', ')')
            # where_supplier_wise_po = " rp.name = '%s'" % str(supplier_wise_po[1])
            print("Group", where_group)

        if customer:
            where_customer = " rp.id in %s" % str(tuple(customer)).replace(',)', ')')
            # where_supplier_wise_po = " rp.name = '%s'" % str(supplier_wise_po[1])
            print(where_customer)

        if location_ids:
            where_branch_ids = " am.branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        if company_ids:
            where_company_ids = " am.company_id = {}".format(company_ids[0])

        datetime_format = '%Y-%m-%d %H:%M:%S'
        utc = datetime.now().strftime(datetime_format)

        query = """
                                      select rp.name as buyer,sum(aml.price_total) as total_amount, rpc.name as buyer_catogry,rb.id from account_move as am
                                    inner join account_move_line aml on am.id = aml.move_id
                                    left join res_partner as rp on am.partner_id=rp.id
                                    left join res_branch rb on am.branch_id = rb.id
                                    left join account_account aa on aml.account_id = aa.id
                                    left join res_partner_res_partner_category_rel as rl on am.partner_id = rl.partner_id
                                    left join res_partner_category rpc on rpc.id = rl.category_id
                                    where am.type = 'out_invoice' and am.state = 'posted'
                                    and {} and aa.internal_group = 'income' and am.invoice_date::DATE between '{}' and '{}'
                                    and {} and {} and {} and {} and {}
                                    group by rp.name,rpc.name,rb.id
                                """.format(where_branch_ids, start_date.strftime(DATETIME_FORMAT),
                                           end_date.strftime(DATETIME_FORMAT),
                                           where_customer_ids, where_company_ids, where_group, where_customer,
                                           where_product_ids)
        self._cr.execute(query=query)
        query_results = self._cr.fetchall()
        data = {
            'result': query_results,
            'start_date': start_date,
            'end_date': end_date,
        }
        print('data is',data)

        # # print(query_results)
        products_dic = dict()
        print('query results is',query_results)
        for query_result in query_results:
            print('each query result',query_result)
            # list_key = tuple([query_result[0], query_result[1], query_result[8], query_result[9]])
            print('query result[2]',query_result[2])
            print('product dict.keys()',products_dic.keys())

            if query_result[2] not in products_dic.keys():
                print('prodcuts dic.keys()',products_dic.keys())
                products_dic[query_result[2]] = list() # 'buyer group' stores in key on dictionary
                print('prodcuts_dic[query_result[2]]',products_dic[query_result[2]])
                products_dic[query_result[2]].append(query_result)
            else:
                products_dic[query_result[2]].append(query_result)
        print(products_dic.keys())
        print(products_dic)

        report_name = 'Sale Buyerwise Report'
        filename = '%s' % (report_name)

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)
        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:I3', report_name, wbf['title_doc'])
        columns_group = [
            # ('SL', 10, 'char', 'char'),
            ('Buyer Category', 30, 'char', 'no'),
        ]
        row = 5

        column_product = [
            ('SL',30,'char','no'),
            ('Buyer Name',50,'char','no'),
            ('Amount',20,'float','float'),
        ]
        gt =0
        for coll in products_dic.keys():
            # worksheet.merge_range('A5:D5', str(coll), wbf['header_orange'])
            col = 0
            column_name = columns_group[0][0]
            column_width = columns_group[0][1]
            worksheet.set_column(col, col, column_width)
            worksheet.write(row - 1, col, column_name, wbf['header_orange'])
            col += 1

            worksheet.write(row - 1, col, coll, wbf['header_orange'])
            col += 1
            col2 = 0
            print('coll is',coll)
            row += 1
            sl2 = 1
            for product in column_product: # for header purpose
                column_name1 = product[0]
                column_width = product[1]
                column_type = product[2]
                worksheet.set_column(col2,col2,column_width)
                worksheet.write(row-1,col2,column_name1,wbf['header_orange']) # always use row-1 because index is starting from 0
                col2 += 1
            row += 1
            am = 0
            for collection in products_dic[coll]:
                col3 = 0
                worksheet.write(row - 1, col3, sl2)
                col3 += 1
                worksheet.write(row-1,col3,collection[0])
                col3 += 1
                worksheet.write(row-1, col3, collection[1])
                row += 1
                sl2 += 1
                am += collection[1]
            row += 1
            worksheet.merge_range('A%s:B%s' % (row-1,row-1), 'Sub Total',wbf['total_orange'])
            # worksheet.merge_range(row - 1, 1, 'Sub Total:',wbf['header_orange'])
            worksheet.write(row - 2, 2, am,wbf['total_orange'])
            row += 1
            gt += am
        row += 1
        worksheet.merge_range('A%s:B%s' % (row - 1, row - 1), 'Grand Total', wbf['total_orange'])
        # worksheet.write(row - 1, 1, 'Grand Total:',wbf['header_orange'])
        worksheet.write(row - 2, 2, gt,wbf['header_orange'])

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


class SalesReportBuyerWise(models.AbstractModel): # this class is using for which which one print on report
    _name = 'report.sale_report.sale_buyerwise_report_view'

    def _get_report_values(self, docids, data=None):
        print(' work here ')
        start_date = data['start_date']
        end_date = data['end_date']
        results = data['result']
        dic_data = dict()
        # brand_dic = dict()
        # print(data['result'])

        print('\n\n\n')
        # invoice_dict = dict()
        # for result in final_list:
        #     if result['invoice'] not in invoice_dict.keys():
        #         invoice_dict[result['invoice']] = list()
        #         invoice_dict[result['invoice']].append(result)
        #     else:
        #         invoice_dict[result['invoice']].append(result)
        # print(invoice_dict)
        # return {
        #     'date_start': start_date,
        #     'date_end': end_date,
        #     'data': invoice_dict,
        # }
        buyer_dict = dict()
        for result in results:
            if result[2] not in buyer_dict.keys():  # result[2] is 'buyer_category' in sql
                buyer_dict[result[2]] = list()
                buyer_dict[result[2]].append(result)
            else:
                buyer_dict[result[2]].append(result)
        print(buyer_dict)

        return {
            'group_value': results,
            'start_date': start_date,
            'end_date': end_date,
            'data': buyer_dict,
        }
