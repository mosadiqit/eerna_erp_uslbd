import base64
from io import BytesIO
from pytz import timezone
import pytz
from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
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


class InvoiceDatewiseSalesSummary(models.TransientModel):
    _name = "inv.date.sale.summary"
    _description = "Invoice date wise sales Summary"

    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone(self.env.user.tz or 'UTC'))

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    product_ids = fields.Many2many('product.product', 'inv_date_sale_sum_product_rel', 'inv_date_sale_sum_id',
                                   'product_id', 'Products')
    categ_ids = fields.Many2many('product.category', 'inv_date_sale_sum_categ_rel', 'inv_date_sale_sum_id',
                                 'categ_id', 'Categories')
    group_ids = fields.Many2many('product.group', 'inv_date_sale_sum_group_rel', 'inv_date_sale_sum_id',
                                 'group_id', 'Group')
    brand_ids = fields.Many2many('product.brand', 'inv_date_sale_sum_brand_rel', 'inv_date_sale_sum_id',
                                 'brand_id', 'Brand')
    model_ids = fields.Many2many('product.model', 'inv_date_sale_sum_model_rel', 'inv_date_sale_sum_id',
                                 'model_id', 'Model')
    location_ids = fields.Many2many('res.branch', 'inv_date_sale_sum_branch_rel', 'inv_date_sale_sum_id',
                                    'branch_id', 'Branch')
    # location_ids = fields.Many2many('res.branch',string='Branch')
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),
                                 default=lambda self: self.env.user.company_id, required=True)
    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Date', required=True, default=fields.Date.today)

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
                'date_start': self.date_start,
                'date_end': self.date_end,
                'company_id': self.company_id.id,
                'branch_ids': self.location_ids,
                'brand_ids': self.brand_ids,
                'product_ids': self.product_ids,
                'group_ids': self.group_ids,
                'model_ids': self.model_ids,
            },
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('sale_report.inv_datewise_sales_sum_report').with_context(landscape=True).report_action(self, data=data)

    def print_excel_report(self):
        data = {
            'form': {
                'date_start': self.date_start,
                'date_end': self.date_end,
                'company_id': self.company_id,
                'branch_ids': self.location_ids,
                'brand_ids': self.brand_ids,
                'product_ids': self.product_ids,
                'group_ids': self.group_ids,
                'model_ids': self.model_ids,
            },
        }
        start_date = data['form']['date_start']
        end_date = data['form']['date_end']
        branch_id = data['form']['branch_ids']
        company_id = data['form']['company_id']

        product_id = data['form']['product_ids']
        group_id = data['form']['group_ids']
        model_id = data['form']['model_ids']
        brand_id = data['form']['brand_ids']

        # start_date = datetime.strptime(date_start, DATE_FORMAT)
        # end_date = datetime.strptime(date_end, DATE_FORMAT)
        # delta = timedelta(days=1)

        # Branch IDS generalize
        # b_id = eval(branch_id.strip('res.branch'))
        # if b_id != ():
        #     b_id = list(b_id)
        #     b_id.append(0)
        #     b_id = tuple(b_id)
        #
        # # Brand IDS generalize
        # brnd_id = eval(brand_id.strip('product.brand'))
        # if brnd_id != ():
        #     brnd_id = list(brnd_id)
        #     brnd_id.append(0)
        #     brnd_id = tuple(brnd_id)
        #
        # # Product IDS generalize
        # prdct_id = eval(product_id.strip('product.product'))
        # if prdct_id != ():
        #     prdct_id = list(prdct_id)
        #     prdct_id.append(0)
        #     prdct_id = tuple(prdct_id)
        #
        # # Group IDS generalize
        # grp_id = eval(group_id.strip('product.group'))
        # if grp_id != ():
        #     grp_id = list(grp_id)
        #     grp_id.append(0)
        #     grp_id = tuple(grp_id)
        #
        # # Model IDS generalize
        # mdl_id = eval(model_id.strip('product.model'))
        # if mdl_id != ():
        #     mdl_id = list(mdl_id)
        #     mdl_id.append(0)
        #     mdl_id = tuple(mdl_id)

        where_company_id = "1=1"
        where_branch_id = "1=1"
        where_product_id = "1=1"
        where_group_id = "1=1"
        where_model_id = "1=1"
        where_brand_id = "1=1"

        if company_id:
            where_company_id = "am.company_id = %s" % str(tuple(company_id.ids)).replace(',)', ')')
        if branch_id:
            where_branch_id = "am.branch_id in %s" % str(tuple(branch_id.ids)).replace(',)', ')')
        if group_id:
            where_group_id = "pg.id in %s" % str(tuple(group_id.ids)).replace(',)', ')')
        if brand_id:
            where_brand_id = "pb.id in %s" % str(tuple(brand_id.ids)).replace(',)', ')')

        if model_id:
            where_model_id = "pm.id in %s" % str(tuple(model_id.ids)).replace(',)', ')')

        if product_id:
            where_product_id = "pp.id in %s" % str(tuple(product_id.ids)).replace(',)', ')')



        # if company_id:
        #     where_company_id = " am.company_id = %s" % company_id
        #
        # if branch_id and b_id != ():
        #     where_branch_id = " am.branch_id in {}".format(b_id)
        #
        # if group_id and grp_id != ():
        #     where_group_id = " pg.id in {}".format(grp_id)
        #
        # if brand_id and brnd_id != ():
        #     where_brand_id = " pb.id in {}".format(brnd_id)
        #
        # if model_id and mdl_id != ():
        #     where_model_id = " pm.id in {}".format(mdl_id)
        #
        # if product_id and prdct_id != ():
        #     where_product_id = " pp.id in {}".format(prdct_id)

        query = '''select am.id,
                am.name as InvoiceNAME,
                am.invoice_date as Invoice_Date,
                so.date_order as SO_Date,
                am.invoice_origin,
                pg.name as ProductGroup,
                pb.name ProductBrand,
                pm.name ProductModel,
                pt.name as ProductName,
        		rp.name as BuyerName,
        		rpp.name as SalesPerson,
                aml.quantity,
                aml.price_unit,
                aml.price_total,
                so.name as SO_Name,
                am.ref as Remarks from account_move am
                inner join account_move_line aml on am.id = aml.move_id
        		left join sale_order so on so.name=am.invoice_origin
                left join product_product pp on aml.product_id = pp.id
                left join product_template pt on pp.product_tmpl_id = pt.id
                left join product_group pg on pt.group_id = pg.id
                left join product_brand pb on pt.brand_id = pb.id
                left join product_model pm on pt.product_model_id = pm.id
                left join res_branch rb on am.branch_id = rb.id
                left join account_account aa on aml.account_id = aa.id
        		left join res_partner rp on rp.id=am.partner_id
        		left join res_users ru on ru.id=am.create_uid
        		left join res_partner rpp on rpp.id=ru.partner_id
                where so.Date_Order::date  between '{}' and '{}' and am.type='{}' and am.state='{}' and  {}
                and {} and {} and {} and {} and {} and aa.internal_group='{}' and so.state='{}'
                order by am.invoice_origin'''.format(start_date.strftime(DATETIME_FORMAT),
                                                     end_date.strftime(DATETIME_FORMAT), 'out_invoice', 'posted',
                                                     where_company_id, where_branch_id, where_brand_id, where_group_id,
                                                     where_model_id, where_product_id, 'income', 'sale')
        self._cr.execute(query=query)
        query_result = self._cr.fetchall()

        query_list = []
        for item in query_result:
            vals = {
                'amID': item[0],
                'InvName': item[1],
                'InvDate': item[2],
                'SoDate': item[3],
                'InvOrigin': item[4],
                'P_Group': item[5],
                'P_Brand': item[6],
                'P_Model': item[7],
                'P_Name': item[8],
                'BuyerName': item[9],
                'SalesPerson': item[10],
                'Qty': item[11],
                'PriceUnit': item[12],
                'Total_Price': item[13],
                'SO_Name': item[14],
                'Remarks': item[15]
            }
            print('item[sodate]',item[3])
            query_list.append(vals)
        report_name = 'Invoice Date Wise Sales Summary Report'
        filename = '%s' % (report_name)
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)
        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:I3', report_name, wbf['title_doc'])

        columns_category = [
            ('Sales Person',20,'char','char'),
            ('Sale Order No',17,'char','char'),
            ('Invoice No',13,'char','char'),
            ('Remarks',13,'char','char'),
            ('Buyer Name',24,'char','char'),
            ('Brand',8,'char','char'),
            ('Group',12,'char','char'),
            ('Product Name',30,'char','char'),
            ('Quantity',9,'float','float'),
            ('Unit Price',10,'float','float'),
            ('Total Value',10,'float','float'),
            ('Invoice Date',20,'char','char'),
            ('Sale Order Date',20,'char','char')
        ]
        row = 5
        col2 = 0
        for coll in columns_category:
            column_name = coll[0]
            column_width = coll[1]
            worksheet.set_column(col2,col2,column_width)
            worksheet.write(row-1,col2,column_name,wbf['header_orange'])
            col2 += 1
        row += 1

        for item in query_list:
            col3 = 0
            worksheet.write(row-1,col3,item['SalesPerson'])
            col3 += 1
            worksheet.write(row-1,col3,item['SO_Name'])
            col3 += 1
            worksheet.write(row-1,col3,item['InvName'])
            col3 += 1
            worksheet.write(row-1, col3, item['Remarks'])
            col3 += 1
            worksheet.write(row-1, col3, item['BuyerName'])
            col3 += 1
            worksheet.write(row-1, col3, item['P_Brand'])
            col3 += 1
            worksheet.write(row-1,col3,item['P_Group'])
            col3 += 1
            worksheet.write(row-1, col3, item['P_Name'])
            col3 += 1
            worksheet.write(row-1, col3, item['Qty'])
            col3 += 1
            worksheet.write(row-1, col3, item['PriceUnit'])
            col3 += 1
            worksheet.write(row-1, col3, item['Total_Price'])
            col3 += 1
            worksheet.write(row-1, col3, str(item['InvDate'])) # in excel report we have to type casting into 'str',
            col3 += 1
            worksheet.write(row-1, col3, str(item['SoDate']))

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








class InvoiceDatewiseSaleSummaryReportView(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.sale_report.invoice_datewise_sale_summary_report_tmp'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        branch_id = data['form']['branch_ids']
        company_id = data['form']['company_id']

        product_id = data['form']['product_ids']
        group_id = data['form']['group_ids']
        model_id = data['form']['model_ids']
        brand_id = data['form']['brand_ids']

        start_date = datetime.strptime(date_start, DATE_FORMAT)
        end_date = datetime.strptime(date_end, DATE_FORMAT)
        delta = timedelta(days=1)

        # Branch IDS generalize
        b_id = eval(branch_id.strip('res.branch'))
        if b_id != ():
            b_id = list(b_id)
            b_id.append(0)
            b_id = tuple(b_id)

        # Brand IDS generalize
        brnd_id = eval(brand_id.strip('product.brand'))
        if brnd_id != ():
            brnd_id = list(brnd_id)
            brnd_id.append(0)
            brnd_id = tuple(brnd_id)

        # Product IDS generalize
        prdct_id = eval(product_id.strip('product.product'))
        if prdct_id != ():
            prdct_id = list(prdct_id)
            prdct_id.append(0)
            prdct_id = tuple(prdct_id)

        # Group IDS generalize
        grp_id = eval(group_id.strip('product.group'))
        if grp_id != ():
            grp_id = list(grp_id)
            grp_id.append(0)
            grp_id = tuple(grp_id)

        # Model IDS generalize
        mdl_id = eval(model_id.strip('product.model'))
        if mdl_id != ():
            mdl_id = list(mdl_id)
            mdl_id.append(0)
            mdl_id = tuple(mdl_id)

        where_company_id = "1=1"
        where_branch_id = "1=1"
        where_product_id = "1=1"
        where_group_id = "1=1"
        where_model_id = "1=1"
        where_brand_id = "1=1"

        if company_id:
            where_company_id = " am.company_id = %s" % company_id

        if branch_id and b_id != ():
            where_branch_id = " am.branch_id in {}".format(b_id)

        if group_id and grp_id != ():
            where_group_id = " pg.id in {}".format(grp_id)

        if brand_id and brnd_id != ():
            where_brand_id = " pb.id in {}".format(brnd_id)

        if model_id and mdl_id != ():
            where_model_id = " pm.id in {}".format(mdl_id)

        if product_id and prdct_id != ():
            where_product_id = " pp.id in {}".format(prdct_id)



        query = '''select am.id,
        am.name as InvoiceNAME,
        am.invoice_date as Invoice_Date,
        so.date_order as SO_Date,
        am.invoice_origin,
        pg.name as ProductGroup,
        pb.name ProductBrand,
        pm.name ProductModel,
        pt.name as ProductName,
		rp.name as BuyerName,
		rpp.name as SalesPerson,
        aml.quantity,
        aml.price_unit,
        aml.price_total,
        so.name as SO_Name,
        am.ref as Remarks from account_move am
        inner join account_move_line aml on am.id = aml.move_id
		left join sale_order so on so.name=am.invoice_origin
        left join product_product pp on aml.product_id = pp.id
        left join product_template pt on pp.product_tmpl_id = pt.id
        left join product_group pg on pt.group_id = pg.id
        left join product_brand pb on pt.brand_id = pb.id
        left join product_model pm on pt.product_model_id = pm.id
        left join res_branch rb on am.branch_id = rb.id
        left join account_account aa on aml.account_id = aa.id
		left join res_partner rp on rp.id=am.partner_id
		left join res_users ru on ru.id=am.create_uid
		left join res_partner rpp on rpp.id=ru.partner_id
        where so.Date_Order::date  between '{}' and '{}' and am.type='{}' and am.state='{}' and  {}
        and {} and {} and {} and {} and {} and aa.internal_group='{}' and so.state='{}'
        order by am.invoice_origin'''.format(start_date.strftime(DATETIME_FORMAT),end_date.strftime(DATETIME_FORMAT),'out_invoice','posted',where_company_id,where_branch_id,where_brand_id,where_group_id,where_model_id,where_product_id,'income','sale')
        self._cr.execute(query=query)
        query_result = self._cr.fetchall()

        query_list = []
        for item in query_result:
            vals ={
                'amID' : item[0],
                'InvName' : item[1],
                'InvDate' : item[2],
                'SoDate' : item[3],
                'InvOrigin' : item[4],
                'P_Group' : item[5],
                'P_Brand' : item[6],
                'P_Model' : item[7],
                'P_Name' : item[8],
                'BuyerName' : item[9],
                'SalesPerson' : item[10],
                'Qty' : item[11],
                'PriceUnit' : item[12],
                'Total_Price' : item[13],
                'SO_Name' : item[14],
                'Remarks' : item[15]
            }
            query_list.append(vals)
        print('query list is',query_list)
        return {
            'query_list' : query_list
        }
