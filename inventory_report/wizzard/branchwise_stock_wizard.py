import xlsxwriter
import base64
from odoo import fields, models, api
from io import BytesIO
from datetime import datetime
from pytz import timezone
import pytz

class BranchWiseReportStock(models.TransientModel):
    _name = "branchwise.report.stock"
    _description = "Branch Wise Stock Report .xlsx"

    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone(self.env.user.tz or 'UTC'))

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    product_ids = fields.Many2many('product.product', 'branchwise_report_stock_product_rel', 'branchwise_report_stock_id',
                                   'product_id', 'Products')
    categ_ids = fields.Many2many('product.category', 'branchwise_report_stock_categ_rel', 'branchwise_report_stock_id',
                                 'categ_id', 'Categories')

    location_ids = fields.Many2many('stock.location', 'branchwise_report_stock_location_rel', 'branchwise_report_stock_id',
                                    'location_id', 'Locations')
    brand_ids=fields.Many2many('product.brand','branchwise_report_stock_brand_rel', 'branchwise_report_stock_id',
                                    'brand_id', 'Brands')
    # model_ids=fields.Many2many('product.model','branchwise_report_stock_model_rel', 'branchwise_report_stock_id',
    #                                 'model_id', 'Models')
    group_ids=fields.Many2many('product.group','branchwise_report_stock_group_rel', 'branchwise_report_stock_id',
                                    'group_id', 'Groups')

    @api.onchange('location_ids')
    def check_users_branch(self):
        location_id = self.env['stock.location'].search([('branch_id', '=', self.env.user.branch_ids.ids)])
        all_location = self.env['stock.location'].search([('usage', '=', 'internal')])
        if self.user_has_groups('stock.group_stock_manager'):
            m_location_id = self.env['stock.location'].search(
                [('usage', '=', 'internal'), ('branch_id', '=', self.env.user.branch_ids.ids)])
            # return [('id','in',m_location_id.ids)]
            return {'domain': {'location_ids': [('id', 'in', m_location_id.ids)]}}
            # self.location_ids = m_location_id
        elif self.user_has_groups('stock.group_stock_user'):
            return {'domain': {'location_ids': [('id', 'in', location_id.ids)]}}

    def print_excel_report(self):
        data = self.read()[0]
        product_ids = data['product_ids']
        print(product_ids)
        categ_ids = data['categ_ids']
        location_ids = data['location_ids']
        location_names = list()
        for location in location_ids:
            location_name = self.env['stock.location'].search([('id','=',location)])
            location_names.append(location_name.complete_name)
        brand_ids = data['brand_ids']
        # model_ids=data['model_ids']
        group_ids=data['group_ids']
        where_product_ids="1=1"
        where_location_ids="1=1"
        where_brand_ids="1=1"
        where_model_ids="1=1"
        where_group_ids = "1=1"
        set_query_condition=''
        print(categ_ids)
        if product_ids:
            where_product_ids = " pp.id in %s" % str(tuple(product_ids)).replace(',)', ')')
        if location_ids:
            where_location_ids = " sl.id in %s" % str(tuple(location_ids)).replace(',)', ')')
        if brand_ids:
            where_brand_ids = " pb.id in %s" % str(tuple(brand_ids)).replace(',)', ')')
        # if model_ids:
        #     where_model_ids = " sl.id in %s" % str(tuple(model_ids)).replace(',)', ')')
        if group_ids:
            where_group_ids = " pg.id in %s" % str(tuple(group_ids)).replace(',)', ')')




        datetime_string = self.get_default_date_model().strftime("%Y-%m-%d %H:%M:%S")
        date_string = self.get_default_date_model().strftime("%Y-%m-%d")
        report_name = 'Branch Wise Stock Report'
        filename = '%s %s' % (report_name, date_string)


        get_location = """select distinct complete_name from stock_location where active='true' and usage='internal' order by 1"""
        self._cr.execute(query=get_location)
        selected_location = self._cr.fetchall()
        columns=[
                ('Product Name', 30, 'char', 'char'),
                ('Group', 20, 'char', 'char'),
                ('Category', 20, 'char', 'char'),
                ('Brand', 20, 'char', 'char'),
                ('Total', 20, 'number', 'char'),
                     ]

        for r in selected_location:
            print(r)
            print(r[0])
            tuple_string=(r[0],30,'number','char')
            columns.append(tuple_string)



        # if location_ids:
        #     columns=[
        #         ('Product Name', 30, 'char', 'char'),
        #         ('Category', 20, 'char', 'char'),
        #         ('Brand', 20, 'char', 'char'),
        #         ('Total', 20, 'number', 'char'),
        #              ]
        #     get_selected_location="""select distinct complete_name from stock_location where active='true' and usage='internal' and id in {} order by 1""".format(str(tuple(location_ids)).replace(',)', ')'))
        #     self._cr.execute(get_selected_location)
        #     result=self._cr.fetchall()
        #     for r in result:
        #         tuple_string=(r[0],30,'number','char')
        #         columns.append(tuple_string)
        #         print(columns)
        # columns = [
        #     # ('No',5,'no','no'),
        #     ('Product Name', 30, 'char', 'char'),
        #     ('Group', 20, 'char', 'char'),
        #     ('Category', 20, 'char', 'char'),
        #     ('Brand', 20, 'char', 'char'),
        #     ('Total', 20, 'number', 'char'),
        #     ('AGB/Stock',20,'number', 'char'),
        #     ('BB/Stock',20,'number', 'char'),
        #     ('CHO/Stock',20,'number', 'char'),
        #     ('ERB/Stock',20,'number', 'char'),
        #     ('Eerna/Stock',20,'number', 'char'),
        #     ('GB/Stock',20,'number', 'char'),
        #     ('JFPB/Stock',20,'number', 'char'),
        #     ('JFPBM/Stock',20,'number', 'char'),
        #     ('Smart/Stock',20,'number', 'char'),
        #     ('Uniso/Stock',20,'number', 'char'),
        #     ('WH/Stock',20,'number', 'char'),
        # ]


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

        query = """
            SELECT "Product","Product_Group","Chategory","Brand",COALESCE("AGB/Stock",0) as "AGB/Stock",COALESCE("BB/Stock",0) as "BB/Stock",
                    COALESCE("CHO/Stock",0) as "CHO/Stock",COALESCE("Digital/Stock",0) as "Digital/Stock",COALESCE("ERB/Stock",0) as "ERB/Stock",COALESCE("Eerna/Stock",0) as "Eerna/Stock",COALESCE("GB/Stock",0) as "GB/Stock",COALESCE("JFPB/Stock",0) as "JFPB/Stock"
                    ,COALESCE("JFPBM/Stock",0) as "JFPBM/Stock",COALESCE("MOH/Stock",0) as "MOH/Stock",COALESCE("PAL/Stock",0) as "PAL/Stock",COALESCE("SAV/Stock",0) as "SAV/Stock",COALESCE("TELCH/Stock",0) as "TELCH/Stock",COALESCE("Smart/Stock",0) as "Smart/Stock",COALESCE("Uniso/Stock",0) as "Uniso/Stock",COALESCE("WH/Stock",0) as "WH/Stock" FROM crosstab
                    ($$ select pt.name as ProductName,pg.name as Product_Group,pc.name as Category,pb.name as Brand,sl.complete_name as StockName,sum(sq.quantity) as Quantity 
                       from product_product pp
                        left join product_template pt on pt.id=pp.product_tmpl_id
                        left join product_brand pb on pb.id=pt.brand_id
                        left join product_category pc on pc.id=pt.categ_id
                        left join product_group pg on pg.id=pt.group_id
                        inner join stock_quant sq on sq.product_id=pp.id
                    inner join stock_location sl on sl.id=sq.location_id where sl.active='true' and sl.usage='internal' and {} and {} and {} and {}   group by 1,2,3,4,5  order by 2,4$$,
                     $$ select distinct complete_name from stock_location where active='true' and usage='internal' 	GROUP BY 1 order by 1$$
                     )
                    AS ("Product" character varying,"Product_Group" character varying,"Chategory" character varying,"Brand" character varying, "AGB/Stock" float8,"BB/Stock" float8,"CHO/Stock" float8,"Digital/Stock" float8,"ERB/Stock" float8,"Eerna/Stock" float8,"GB/Stock" float8,"JFPB/Stock" float8,
			   "JFPBM/Stock" float8,"MOH/Stock" float8,"PAL/Stock" float8,"SAV/Stock" float8,"TELCH/Stock" float8,"Smart/Stock" float8,"Uniso/Stock" float8,"WH/Stock" float8)
        """.format(where_product_ids,where_brand_ids,where_location_ids,where_group_ids)

        # self._cr.execute(query % (hours, hours, where_product_ids))
        self._cr.execute(query)
        result = self._cr.fetchall()
        print(result)

        total=0
        new_result=[]
        for r in result:
            total=sum(list(r[4:]))
            r=r[:4]+(total,)+r[4:]
            new_result.append(r)
        print(new_result)

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
        for res in new_result:

            col = 0
            for column in columns:
                column_name = column[0]
                column_width = column[1]
                column_type = column[2]
                if column_type == 'char':
                    col_value = res[col ] if res[col ] else ''
                    wbf_value = wbf['content']
                elif column_type == 'no':
                    col_value = no
                    wbf_value = wbf['content']
                elif column_type == 'datetime':
                    col_value = res[col - 1].strftime('%Y-%m-%d %H:%M:%S') if res[col - 1] else ''
                    wbf_value = wbf['content']
                else:
                    col_value = res[col ] if res[col ] else 0
                    if column_type == 'float':
                        wbf_value = wbf['content_float']
                    else:  # number
                        wbf_value = wbf['content_number']
                    column_float_number[col] = column_float_number.get(col, 0) + col_value

                worksheet.write(row - 1, col, col_value, wbf_value)

                col += 1

            row += 1
            no += 1

        q="""select sum(sq.quantity),sl.complete_name from product_product pp
                left join product_template pt on pt.id=pp.product_tmpl_id
                left join product_brand pb on pb.id=pt.brand_id
                inner join stock_quant sq on sq.product_id=pp.id
                left join product_group pg on pg.id=pt.group_id
                inner join stock_location sl on sl.id=sq.location_id where sl.active='true' and sl.usage='internal'  and {} and {} and {}  GROUP BY 2 order by 2""".format(where_location_ids,where_product_ids,where_brand_ids,where_group_ids)
        self._cr.execute(query=q)
        grand_total=self._cr.fetchall()
        grand_total_value=0.0
        c=0
        for res in grand_total:
            print(res[0])
            if res[0]!=None:
                grand_total_value=grand_total_value+res[0]
            # c+=1
        # worksheet.merge_range('A%s:B%s' % (row, row), 'Grand Total', wbf['total_orange'])
        worksheet.merge_range('A%s:B%s' % (row,row), '', wbf['total_orange'])
        worksheet.merge_range('C%s:D%s' % (row, row), 'Grand Total', wbf['total_orange'])
        val=0
        col_name=""
        element_count=len(grand_total)

        for x in range(len(columns)):
            if x in (0, 1,2,3):
                continue
            print(columns[x][0])
            if x==4:
                worksheet.write(row - 1, x, grand_total_value, wbf['total_orange'])
            if val<=element_count-1 :
                col_name=grand_total[val][1]

            if columns[x][0]==col_name:
                print(grand_total[val][0])
                if grand_total[val][0]!=None:
                    worksheet.write(row-1, x,grand_total[val][0] , wbf['total_orange'])
                    val += 1
                else:
                    worksheet.write(row - 1, x, 0, wbf['total_orange'])
                    val += 1
            if columns[x][0] != col_name and x>4:
                worksheet.write(row - 1, x, 0, wbf['total_orange'])

        # for x in range(len(columns)):
        #     if x in (0, 1):
        #         continue
        #     column_type = columns[x][3]
        #     if column_type == 'char':
        #         worksheet.write(row - 1, x, '', wbf['total_orange'])
        #     else:
        #         if column_type == 'float':
        #             wbf_value = wbf['total_float_orange']
        #         else:  # number
        #             wbf_value = wbf['total_number_orange']
        #         if x in column_float_number:
        #             worksheet.write(row - 1, x, column_float_number[x], wbf_value)
        #         else:
        #             worksheet.write(row - 1, x, 0, wbf_value)

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
