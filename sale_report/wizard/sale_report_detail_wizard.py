import xlsxwriter
import base64
from odoo import fields, models, api
from io import BytesIO
from datetime import datetime
from pytz import timezone
import pytz


class SaleReportDetail(models.TransientModel):
    _name = "sale.report.detail"
    _description = "Sale Detail Report .xlsx"

    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone(self.env.user.tz or 'UTC'))

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    product_ids = fields.Many2many('product.product', 'sale_report_detail_product_rel', 'sale_report_detail_id',
                                   'product_id', 'Products')
    categ_ids = fields.Many2many('product.category', 'sale_report_detail_categ_rel', 'sale_report_detail_id',
                                 'categ_id', 'Categories')
    group_ids = fields.Many2many('product.group', 'sale_report_detail_group_rel', 'sale_report_detail_id',
                                 'group_id', 'Group')
    brand_ids = fields.Many2many('product.brand', 'sale_report_detail_brand_rel', 'sale_report_detail_id',
                                 'brand_id', 'Brand')
    model_ids = fields.Many2many('product.model', 'sale_report_detail_model_rel', 'sale_report_detail_id',
                                 'model_id', 'Model')
    location_ids = fields.Many2many('res.branch', 'ms_report_branch_rel', 'sale_report_detail_id',
                                    'branch_id', 'Branch')
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),
                                 default=lambda self: self.env.user.company_id,required=True)
    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Date', required=True, default=fields.Date.today)



    def _get_companies(self):
        query="""select * from res_company_users_rel where user_id={}""".format(self.env.user.id)
        self._cr.execute(query=query)
        allowed_companies=self._cr.fetchall()
        allowed_company=[]
        for company in allowed_companies:
            allowed_company.append(company[0])
        return  [('id', 'in', allowed_company)]

    def print_excel_report(self):
        data = self.read()[0]
        product_ids = data['product_ids']
        categ_ids = data['categ_ids']
        group_ids = data['group_ids']
        brand_ids = data['brand_ids']
        model_ids = data['model_ids']
        location_ids = data['location_ids']
        start_date = data['date_start']
        end_date = data['date_end']
        company_id = data['company_id']

        print(company_id[0])

        where_group_ids = " 1=1 "
        where_brand_ids = " 1=1 "
        where_model_ids = " 1=1 "
        where_branch_ids= " 1=1 "
        where_company_id="1=1"
        if categ_ids:
            product_ids = self.env['product.product'].search([('categ_id', 'in', categ_ids)])
            product_ids = [prod.id for prod in product_ids]
        where_product_ids = " 1=1 "
        where_product_ids2 = " 1=1 "
        if product_ids:
            where_product_ids = " aml.product_id in %s" % str(tuple(product_ids)).replace(',)', ')')
            where_product_ids2 = " product_id in %s" % str(tuple(product_ids)).replace(',)', ')')
        # location_ids2 = self.env['res.branch']
        # ids_location = [loc.id for loc in location_ids2]
        # where_location_ids = " so.branch_id in %s" % str(tuple(ids_location)).replace(',)', ')')
        # where_location_ids2 = " branch_id in %s" % str(tuple(ids_location)).replace(',)', ')')
        # if location_ids:
        #     where_location_ids = " so.branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        #     where_location_ids2 = " branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        if group_ids:
            where_group_ids = " pg.id in %s" % str(tuple(group_ids)).replace(',)', ')')
        if brand_ids:
            where_brand_ids = " pb.id in %s" % str(tuple(brand_ids)).replace(',)', ')')
        if model_ids:
            where_model_ids = " pm.id in %s" % str(tuple(model_ids)).replace(',)', ')')
        if location_ids:
            where_branch_ids = " so.branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        if company_id:
            where_company_id = " so.company_id = {}".format(company_id[0])

        datetime_string = self.get_default_date_model().strftime("%Y-%m-%d %H:%M:%S")
        date_string = self.get_default_date_model().strftime("%Y-%m-%d")
        report_name = 'Sale Detail Report'
        filename = '%s %s' % (report_name, date_string)

        columns = [
            ('No', 5, 'no', 'no'),
            ('Branch', 30, 'char', 'char'),
            ('Sales Person', 20, 'char', 'char'),
            ('Buyer Group', 20, 'char', 'char'),
            ('Sales Order', 20, 'char', 'char'),
            ('Invoice', 20, 'char', 'char'),
            ('Remarks', 30, 'char', 'char'),
            ('Buyer', 20, 'char', 'char'),
            ('Brand', 30, 'char', 'char'),
            ('Group', 30, 'char', 'char'),
            ('Product', 30, 'char', 'char'),
            ('Quantity', 20, 'float', 'float'),
            ('Unit Price', 20, 'float', 'float'),
            ('Total Price', 20, 'float', 'float'),
            ('Invoice Date', 20, 'datetime', 'char'),
            ('Sales Date', 20, 'datetime', 'char'),
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

        # query = """
        #     select b.name as branch, e.name as salesperson,pc.Name as BuyerGroup,so.name as saleorder,ac.name as invoice,ac.ref as Remarks,p.name as buyer,pb.name as brand,pg.name as group,ol.name as product,ol.qty_invoiced,ol.price_unit,ol.price_total,ac.create_date as invoicedate,so.create_date as sodate
        #     from sale_order_line as ol
        #     left join sale_order as so on ol.order_id = so.id
        #     left join res_partner p on so.partner_id = p.id
        #     left join res_partner_res_partner_category_rel as pcr on pcr.partner_id=p.id
		# 	left join res_partner_category as pc on pcr.category_id=pc.id
		# 	left join product_product as pd on ol.product_id = pd.id
        #     left join product_template as pt on pd.product_tmpl_id = pt.id
        #     left join product_group as pg on pt.group_id = pg.id
        #     left join product_brand as pb on pt.brand_id = pb.id
        #     left join product_model as pm on pt.product_model_id = pm.id
        #     left join account_move as ac on so.name = ac.invoice_origin
        #     left join account_move_line aml on ac.id = aml.move_id
        #     left join hr_employee as e on so.create_uid = e.user_id
        #     left join res_branch as b on so.branch_id = b.id
        #     where acm.type = 'out_invoice' and ac.state='posted' and account_root_id=52048 and ac.invoice_date::date between '{}' and '{}' and
        #         {} and {} and {} and {} and {} and {}
        #     ORDER BY
        #         sodate
        # """.format(start_date,end_date,where_product_ids, where_branch_ids,where_group_ids,where_brand_ids,where_model_ids,where_company_id)

        query = """
                    select b.name as branch, e.name as salesperson,pc.Name as BuyerGroup,so.name as saleorder,ac.name as invoice,ac.ref as Remarks,p.name as buyer,pb.name as brand,pg.name as group,aml.name as product,aml.quantity as qty_invoiced,aml.price_unit,aml.price_total,ac.create_date as invoicedate,so.create_date as sodate
                    from sale_order so
                    left join account_move as ac on so.name = ac.invoice_origin
                    left join account_move_line aml on ac.id = aml.move_id
                    left join res_partner p on so.partner_id = p.id
                    left join res_partner_res_partner_category_rel as pcr on pcr.partner_id=p.id
                    left join res_partner_category as pc on pcr.category_id=pc.id
                    left join product_product as pd on aml.product_id = pd.id
                    left join product_template as pt on pd.product_tmpl_id = pt.id
                    left join product_group as pg on pt.group_id = pg.id
                    left join product_brand as pb on pt.brand_id = pb.id
                    left join product_model as pm on pt.product_model_id = pm.id
                    left join hr_employee as e on so.create_uid = e.user_id
                    left join res_branch as b on so.branch_id = b.id
                    where ac.type = 'out_invoice' and ac.state='posted' and account_root_id=52048 and ac.invoice_date::date between '{}' and '{}' and
                        {} and {} and {} and {} and {} and {}
                    ORDER BY 
                        sodate
                """.format(start_date, end_date, where_product_ids, where_branch_ids, where_group_ids, where_brand_ids,
                           where_model_ids, where_company_id)
        self._cr.execute(query)
        # self._cr.execute(query % (where_product_ids, where_location_ids,where_group_ids,where_brand_ids,where_model_ids))
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