from odoo import fields, models, api
from io import BytesIO
from datetime import datetime
from pytz import timezone
import pytz
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


class SaleGroupBrandItemWise(models.TransientModel):
    _name = "sale.report.group_item_wise"
    _description = "Sale group report item wise"
    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename',readonly=True)

    def _get_companies(self):
        query = """select * from res_company_users_rel where user_id={}""".format(self.env.user.id)
        self._cr.execute(query=query)
        allowed_companies = self._cr.fetchall()
        allowed_company = []
        print(allowed_companies)
        for company in allowed_companies:
            allowed_company.append(company[0])
        return [('id', 'in', allowed_company)]

    def group_item_wise_print_pdf_report(self):
        data = self.read()[0]
        product_ids = data['product_ids']
        categ_ids = data['categ_ids']
        group_ids = data['group_ids']
        brand_ids = data['brand_ids']
        model_ids = data['model_ids']
        location_ids = data['location_ids']
        start_date = data['start_date']
        end_date = data['end_date']
        company_id = data['company_id']
        # start_date = start_date.strftime('%Y-%M-%D')

        print(type(start_date), end_date)

        where_group_ids = " 1=1 "
        where_brand_ids = " 1=1 "
        where_model_ids = " 1=1 "
        where_branch_ids = " 1=1 "
        where_company_id = "1=1"

        if categ_ids:
            product_ids = self.env['product.product'].search([('categ_id', 'in', categ_ids)])
            product_ids = [prod.id for prod in product_ids]
        where_product_ids = " 1=1 "
        where_product_ids2 = " 1=1 "
        if product_ids:
            where_product_ids = " reg.product_id in %s" % str(tuple(product_ids)).replace(',)', ')')
            where_product_ids2 = " product_id in %s" % str(tuple(product_ids)).replace(',)', ')')
        # location_ids2 = self.env['res.branch']
        # ids_location = [loc.id for loc in location_ids2]
        # where_location_ids = " so.branch_id in %s" % str(tuple(ids_location)).replace(',)', ')')
        # where_location_ids2 = " branch_id in %s" % str(tuple(ids_location)).replace(',)', ')')
        # if location_ids:
        #     where_location_ids = " so.branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        #     where_location_ids2 = " branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        if group_ids:
            where_group_ids = " reg.group_id in %s" % str(tuple(group_ids)).replace(',)', ')')
        if brand_ids:
            where_brand_ids = " reg.brand_id in %s" % str(tuple(brand_ids)).replace(',)', ')')
        if model_ids:
            where_model_ids = " reg.product_model_id in %s" % str(tuple(model_ids)).replace(',)', ')')
        if location_ids:
            where_branch_ids = " branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        if company_id:
            where_company_id = " company_id = {}".format(company_id[0])

        # datetime_string = self.get_default_date_model().strftime("%Y-%m-%d %H:%M:%S")
        # date_string = self.get_default_date_model().strftime("%Y-%m-%d")

        # query =""" select b.name as branch,pb.name as brand,pg.name as group,ol.name as product,ol.qty_invoiced,ol.price_unit,ol.price_total,ac.create_date as invoicedate,so.create_date as sodate
        #     from sale_order_line as ol
        #     left join sale_order as so on ol.order_id = so.id
        # 	 left join product_product as pd on ol.product_id = pd.id
        #     left join product_template as pt on pd.product_tmpl_id = pt.id
        #     left join product_group as pg on pt.group_id = pg.id
        #     left join product_brand as pb on pt.brand_id = pb.id
        #     left join product_model as pm on pt.product_model_id = pm.id
        #     left join account_move as ac on so.name = ac.invoice_origin
        #     left join res_branch as b on so.branch_id = b.id
        #     where so.invoice_status = 'invoiced' and ac.state='posted'
        # 	and ac.create_date between {} and {}
        # 	and {} and {} and {} and {} and {} and {} """

        query = """select  *  from
                (select brand.id as brand_id , brand.name as brand , grop.id as group_id , grop.name as group_name,pro_p.id as
                 product_id, pro_t.name as product_name,invoice_line.quantity ,invoice_line.total,pro_t.product_model_id 
                 from product_product as pro_p, product_template as pro_t,
                (select product_id  ,count(id) as quantity,sum(price_subtotal)as total from sale_order_line where 
                invoice_status = 'invoiced'
                and order_id in (select id from sale_order where {} and date_order::date between '{}' and '{}')
                group by product_id)as invoice_line ,
                product_group as grop , product_brand as brand where pro_t.id = pro_p.product_tmpl_id and 
                pro_p.id= invoice_line.product_id and grop.id = pro_t.group_id and pro_t.brand_id=brand.id)as reg where
                 {} and {} and {} and {}  order by group_id""".format(
            where_branch_ids, start_date, end_date, where_group_ids, where_brand_ids, where_model_ids,
            where_product_ids)
        print('print pdf report')
        self._cr.execute(query)
        result = self._cr.fetchall()
        # print(result)
        data = {
            'result': result,
            'star_date': start_date,
            'end_date': end_date
        }
        return self.env.ref('sale_report.group_brand_wise_report').report_action(
            self, data=data)

    start_date = fields.Date(string="Start Date", default=datetime.now())
    end_date = fields.Date(string='End Date', default=datetime.now())
    product_ids = fields.Many2many('product.product', 'product_group_and_item_wise_rel', string='Products')
    categ_ids = fields.Many2many('product.category', 'product_catg_and_group_wise_rel', string='Categories')
    group_ids = fields.Many2many('product.group', 'product_group_id_group_bran_rel', string='Group')
    brand_ids = fields.Many2many('product.brand', 'product_brand_id_and_group_brad_rel', string='Brand')
    model_ids = fields.Many2many('product.model', 'product_model_and_group_brand_rel', string='Model')
    location_ids = fields.Many2many('res.branch', 'product_location_and_group_brand_rel', string='Branch')
    company_id = fields.Many2one('res.company', 'Company',
                                 domain=lambda self: self._get_companies(),
                                 default=lambda self: self.env.user.company_id, required=True)

    def print_excel_report(self):
        data = self.read()[0]
        product_ids = data['product_ids']
        categ_ids = data['categ_ids']
        group_ids = data['group_ids']
        brand_ids = data['brand_ids']
        model_ids = data['model_ids']
        location_ids = data['location_ids']
        start_date = data['start_date']
        end_date = data['end_date']
        company_id = data['company_id']
        # start_date = start_date.strftime('%Y-%M-%D')

        print(type(start_date), end_date)

        where_group_ids = " 1=1 "
        where_brand_ids = " 1=1 "
        where_model_ids = " 1=1 "
        where_branch_ids = " 1=1 "
        where_company_id = "1=1"

        if categ_ids:
            product_ids = self.env['product.product'].search([('categ_id', 'in', categ_ids)])
            product_ids = [prod.id for prod in product_ids]
        where_product_ids = " 1=1 "
        where_product_ids2 = " 1=1 "
        if product_ids:
            where_product_ids = " reg.product_id in %s" % str(tuple(product_ids)).replace(',)', ')')
            where_product_ids2 = " product_id in %s" % str(tuple(product_ids)).replace(',)', ')')
        # location_ids2 = self.env['res.branch']
        # ids_location = [loc.id for loc in location_ids2]
        # where_location_ids = " so.branch_id in %s" % str(tuple(ids_location)).replace(',)', ')')
        # where_location_ids2 = " branch_id in %s" % str(tuple(ids_location)).replace(',)', ')')
        # if location_ids:
        #     where_location_ids = " so.branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        #     where_location_ids2 = " branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        if group_ids: # we read 'data' so 'group_ids' return list not object
            where_group_ids = " reg.group_id in %s" % str(tuple(group_ids)).replace(',)', ')')
        if brand_ids:
            where_brand_ids = " reg.brand_id in %s" % str(tuple(brand_ids)).replace(',)', ')')
        if model_ids:
            where_model_ids = " reg.product_model_id in %s" % str(tuple(model_ids)).replace(',)', ')')
        if location_ids:
            where_branch_ids = " branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        if company_id:
            where_company_id = " company_id = {}".format(company_id[0])

        # datetime_string = self.get_default_date_model().strftime("%Y-%m-%d %H:%M:%S")
        # date_string = self.get_default_date_model().strftime("%Y-%m-%d")


        query = """select  *  from
                        (select brand.id as brand_id , brand.name as brand , grop.id as group_id , grop.name as group_name,pro_p.id as
                         product_id, pro_t.name as product_name,invoice_line.quantity ,invoice_line.total,pro_t.product_model_id
                         from product_product as pro_p, product_template as pro_t,
                        (select product_id  ,count(id) as quantity,sum(price_subtotal)as total from sale_order_line where
                        invoice_status = 'invoiced'
                        and order_id in (select id from sale_order where {} and date_order::date between '{}' and '{}')
                        group by product_id)as invoice_line ,
                        product_group as grop , product_brand as brand where pro_t.id = pro_p.product_tmpl_id and
                        pro_p.id= invoice_line.product_id and grop.id = pro_t.group_id and pro_t.brand_id=brand.id)as reg where
                         {} and {} and {} and {}  order by group_id""".format(
            where_branch_ids, start_date, end_date, where_group_ids, where_brand_ids, where_model_ids,
            where_product_ids)
        print('print pdf report')
        self._cr.execute(query)
        result = self._cr.fetchall()
        # print(result)
        data = {
            'result': result,
            'star_date': start_date,
            'end_date': end_date
        }

        dic_data = dict()
        brand_dic = dict()
        # print(data['result'])
        for reslt in data['result']:
            print(reslt[3])
            if reslt[3] not in dic_data.keys():
                dic_data[reslt[3]] = dict()
            if reslt[1] not in dic_data[reslt[3]].keys():
                brand_dic[reslt[3]] = set()  # 'brand_dic' is not important here
                brand_dic[reslt[3]].add(reslt[1])
                dic_data[reslt[3]][reslt[1]] = list()
                dic_data[reslt[3]][reslt[1]].append(reslt)  # 'reslt' is a list,which append on another list
            else:
                brand_dic[reslt[3]].add(reslt[1])
                dic_data[reslt[3]][reslt[1]].append(reslt)

        report_name = 'Group Brand Item Wise Summary'
        filename = '%s' % (report_name)
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf,workbook = self.add_workbook_format(workbook)
        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:I3', report_name, wbf['title_doc'])

        columns_category = [
            ('Category',30,'char','char'),
            ('Category2',70,'char','char')
        ]
        columns_brand = [
            ('Brand',20,'char','char'),
            ('Brand2',70,'char','char')
        ]

        columns = [
            ('SL',30,'char','no'),
            ('Description',70,'char','no'),
            ('Qty',19,'float','float'),
            ('Value',14,'float','float'),
        ]
        row = 5
        # col = 0
        # for column in columns:
        #
        # row += 1
        print('dic data keys',dic_data.keys())
        for categ in dic_data.keys():
            print('categ is',categ)
            column_categ = columns_category[0][0]
            column_categ_width = columns_category[0][1]
            worksheet.set_column(0,0,column_categ_width) # (0,0) means corner left position
            worksheet.write(row-1,0,column_categ, wbf['header_orange'])
            column_categ2_width = columns_category[1][1]
            worksheet.set_column(0,1,column_categ2_width) # (0,1) means right position after corner left
            worksheet.write(row-1, 1, categ, wbf['header_orange'])
            row += 1
            print('row is',row)
            gt = 0
            for brand in dic_data[categ]:
                column_brand = columns_brand[0][0]
                column_brand_width = columns_brand[0][1]
                column_brand2_width = columns_brand[1][1]
                worksheet.set_column(0, 0, column_brand_width)
                worksheet.write(row - 1, 0, column_brand, wbf['header_orange'])
                worksheet.set_column(0,1,column_brand2_width)
                worksheet.write(row - 1, 1, brand,wbf['header_orange'])
                row += 1
                col3 = 0
                for coll in columns:
                    column_name = coll[0]
                    column_width = coll[1]
                    column_type = coll[2]
                    worksheet.set_column(col3,col3,column_width)
                    worksheet.write(row-1,col3,column_name,wbf['header_orange'])
                    col3 += 1
                row += 1
                sl = 1
                am = 0
                for item in dic_data[categ][brand]:
                    col4 = 0
                    worksheet.write(row-1,col4,sl)
                    col4 += 1
                    worksheet.write(row-1,col4,item[5])
                    col4 += 1
                    worksheet.write(row - 1,col4,item[6])
                    col4 += 1
                    worksheet.write(row-1,col4,item[7])
                    sl += 1
                    am += item[7]
                    row += 1


                worksheet.write(row - 1, 2, 'Brand Sub Total:', wbf['header_orange'])
                worksheet.write(row - 1, 3, am, wbf['header_orange'])
                row += 1
                gt += am

            worksheet.write(row - 1, 2, 'Category Sub Total:', wbf['header_orange'])
            worksheet.write(row - 1, 3, gt, wbf['header_orange'])
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






            # col = 0
            # for coll in columns:
            #     column_name = coll[0]
            #     column_width = coll[1]
            #     column_type = coll[2]
            #     worksheet.set_column(col, col, column_width)
            #     worksheet.write(row - 1, col, column_name, wbf['header_orange'])
            #     col += 1
            # row += 1
            # col2 = 0
            # for brand in dic_data['categ']:





class GroupBrandWiseReport(models.AbstractModel):
    _name = 'report.sale_report.group_brand_wise_report_view'

    def _get_report_values(self, docids, data=None):
        print(' work here ')
        start_date = data['star_date']
        end_date = data['end_date']

        dic_data = dict()
        brand_dic = dict()
        # print(data['result'])
        for reslt in data['result']:
            print(reslt[3])
            if reslt[3] not in dic_data.keys():
                dic_data[reslt[3]] = dict()
            if reslt[1] not in dic_data[reslt[3]].keys():
                brand_dic[reslt[3]] = set() # 'brand_dic' is not important here
                brand_dic[reslt[3]].add(reslt[1])
                dic_data[reslt[3]][reslt[1]] = list()
                dic_data[reslt[3]][reslt[1]].append(reslt) # 'reslt' is a list,which append on another list
            else:
                brand_dic[reslt[3]].add(reslt[1])
                dic_data[reslt[3]][reslt[1]].append(reslt)

        # print('\n\n\n')
        # print('dictionary : brand __', dic_data[:5])
        # print('brand dic', brand_dic)

        for categ in dic_data.keys():
            print('categ is',categ)

        return {
            'groups': list(brand_dic.keys()),
            'brands': brand_dic,
            'data': dic_data,
            'start_date': start_date,
            'end_date': end_date

        }
