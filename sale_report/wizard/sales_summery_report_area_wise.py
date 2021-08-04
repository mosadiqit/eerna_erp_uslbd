# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, BytesIO, xlsxwriter, base64


class AreaWiseSalesReportWizard(models.TransientModel):
    _name = 'area.sales.summary.report.wizard'

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Date', required=True, default=fields.Date.today)
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self:self._get_companies(),default=lambda self: self.env.user.company_id,required=True)
    branch_ids = fields.Many2one( 'res.branch',string='Branch')
    area = fields.Many2many('customer.area.setup', string='Area')



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
                'branch_id': self.branch_ids.id,
                'branch_name': self.branch_ids.name,
            },
        }
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        branch_id = data['form']['branch_id']
        branch_name = data['form']['branch_name']
        company_id = data['form']['company_id']

        if branch_id:
            branch_id = " ap.branch_id = %s" % branch_id
        else:
            branch_id = "1=1"

        if company_id:
            company_id = " am.company_id = %s" % company_id
        else:
            company_id = "1=1"

        query = """select ca.area_name,p.name as customer,sum(l.credit) TotalSalesAmount from account_move m
                    left join account_move_line l on m.id=l.move_id
                    left join res_partner p on p.id=m.partner_id
                    inner join customer_area_setup ca on ca.id=p.customer_area
                    left join res_branch br on br.id=ap.branch_id
                    where account_root_id=52048 and m.state='posted' and {} and m.date::date between '{}' and '{}' and {} and m.company_id=br.company_id
                    group by ca.area_name,p.name
                    order by ca.area_name,p.name
                   """.format(branch_id, date_start, date_end, company_id)

        self._cr.execute(query=query)
        query_result = self._cr.fetchall()
        area_sales = dict()
        for collection in query_result:

            print(collection[0])
            area = collection[0]
            if area not in area_sales.keys():
                area_sales[area] = dict()
                area_sales[area].append(collection)
            else:
                area_sales[area] = list()
                area_sales[area].append(collection)

        # excel start
    #     report_name = 'Area Wise Sales'
    #     filename = '%s' % (report_name)
    #     fp = BytesIO()
    #     workbook = xlsxwriter.Workbook(fp)
    #     wbf, workbook = self.add_workbook_format(workbook)
    #     worksheet = workbook.add_worksheet(report_name)
    #     worksheet.merge_range('A2:D3', report_name, wbf['title_doc'])
    #     columns_group = [
    #         ('SL', 20, 'no', 'no'),
    #         ('Area', 20, 'char', 'char'),
    #         ('Customer', 30, 'char', 'char'),
    #         ('Sales Amount', 30, 'char', 'char'),
    #
    #     ]
    #     col = 0
    #     row = 4
    #
    #     for group in columns_group:
    #         # col=0
    #         column_name1 = group[0]
    #         column_width = group[1]
    #         column_type = group[2]
    #         worksheet.set_column(col, col, column_width)
    #         worksheet.write(row - 1, col, column_name1, wbf['header_orange'])
    #         # worksheet.merge_range('A2:I3', column_name, wbf['header_orange'])
    #         col += 1
    #         # row += 1
    #
    #     row += 1
    #     for date_group in area_sales.keys():
    #         worksheet.merge_range('A%s:G%s' % (row, row), str(date_group), wbf['header_orange'])
    #         row += 1
    #         # col1 = 0
    #         print("date_group:", date_group)
    #         subtotal_date_wise = 0
    #         for branch in area_sales[date_group]:
    #             worksheet.merge_range('A%s:G%s' % (row, row), str(branch), wbf['header_orange'])
    #             row += 1
    #             # col1 = 0
    #             print("branch:", branch)
    #             b_subtotal_tt_wise=b_subtotal_Checks_wise=b_subtotal_PDC_wise=b_subtotal_Electronic_wise=b_subtotal_Cash_wise=0
    #
    #             subtotal_branch_wise = 0
    #             for type in area_sales[date_group][branch]:
    #                 worksheet.merge_range('A%s:G%s' % (row, row), str(type), wbf['header_orange'])
    #                 row += 1
    #                 # col1 = 0
    #                 print("type:", type)
    #                 subtotal_type_wise = 0
    #                 # subtotal_bank_wise=0
    #                 for bank in area_sales[date_group][branch][type]:
    #                     worksheet.merge_range('A%s:G%s' % (row, row), str(bank), wbf['header_orange'])
    #                     row += 1
    #                     # col1 = 0
    #                     print("bank:", bank)
    #                     sl = 1
    #                     subtotal_bank_wise = 0
    #                     for collection in area_sales[date_group][branch][type][bank]:
    #                         col2 = 0
    #                         worksheet.write(row - 1, col2, sl)
    #                         sl += 1
    #                         col2 += 1
    #                         worksheet.write(row - 1, col2, collection[3])
    #                         col2 += 1
    #                         worksheet.write(row - 1, col2, collection[4])
    #                         col2 += 1
    #                         worksheet.write(row - 1, col2, collection[5])
    #                         col2 += 1
    #                         worksheet.write(row - 1, col2, collection[6])
    #                         col2 += 1
    #                         worksheet.write(row - 1, col2, collection[7])
    #                         col2 += 1
    #                         worksheet.write(row - 1, col2, collection[8])
    #                         row+=1
    #                         print("collection:", collection)
    #                         subtotal_bank_wise += collection[8]
    #                         subtotal_type_wise += collection[8]
    #                         subtotal_branch_wise += collection[8]
    #                         subtotal_date_wise += collection[8]
    #                     print("subtotal_bank_wise",subtotal_bank_wise)
    #                     row+=1
    #
    #                     worksheet.write(row - 1, 5, 'Sub Total of'+ " "+ str(bank) + " : ")
    #                     worksheet.write(row - 1, 6, subtotal_bank_wise)
    #                     row += 1
    #                 # b_subtotal_bank_wise=subtotal_bank_wise
    #                 if type == "TT":
    #                     b_subtotal_tt_wise = subtotal_type_wise
    #                 if type == "Checks":
    #                     b_subtotal_Checks_wise = subtotal_type_wise
    #                 if type == "PDC":
    #                     b_subtotal_PDC_wise = subtotal_type_wise
    #                 if type == "Electronic":
    #                     b_subtotal_Electronic_wise = subtotal_type_wise
    #                 if type == "Cash":
    #                     b_subtotal_Cash_wise = subtotal_type_wise
    #                 worksheet.write(row - 1, 5, 'Total' + " "+ str(type)+" " + "Amount : ")
    #                 worksheet.write(row - 1, 6, subtotal_type_wise)
    #                 row += 1
    #
    #             worksheet.merge_range('A%s:G%s' % (row, row),"Total On"+" "+str(branch), wbf['title_doc'])
    #             row += 1
    #             if b_subtotal_tt_wise>0:
    #                 worksheet.write(row - 1, 5, 'Total TT Amount:' )
    #                 worksheet.write(row - 1, 6, b_subtotal_tt_wise)
    #                 row += 1
    #             if b_subtotal_Checks_wise > 0:
    #                 worksheet.write(row - 1, 5, 'Total Cheque Amount:')
    #                 worksheet.write(row - 1, 6, b_subtotal_Checks_wise)
    #                 row += 1
    #             if b_subtotal_PDC_wise > 0:
    #                 worksheet.write(row - 1, 5, 'Total PDC Amount:')
    #                 worksheet.write(row - 1, 6, b_subtotal_PDC_wise)
    #                 row += 1
    #             if b_subtotal_Electronic_wise > 0:
    #                 worksheet.write(row - 1, 5, 'Total Electronic Amount:')
    #                 worksheet.write(row - 1, 6, b_subtotal_Electronic_wise)
    #                 row += 1
    #             if b_subtotal_Cash_wise > 0:
    #                 worksheet.write(row - 1, 5, 'Total Cash Amount:')
    #                 worksheet.write(row - 1, 6, b_subtotal_Cash_wise)
    #                 row += 1
    #
    #
    #             worksheet.write(row - 1, 5, 'Total Amount On' + " " + str(branch) + " : ")
    #             worksheet.write(row - 1, 6, subtotal_branch_wise)
    #             row += 2
    #         worksheet.merge_range('A%s:G%s' % (row, row), "Total Of" + " " + str(date_group), wbf['title_doc'])
    #         row += 1
    #         worksheet.write(row - 1, 5, 'Total Amount On' + " " + str("("+date_group+")") + " : ")
    #         worksheet.write(row - 1, 6, subtotal_date_wise)
    #         row += 2
    #     worksheet.merge_range('A%s:G%s' % (row, row), "Grand Total", wbf['title_doc'])
    #     row +=1
    #     for total in total_collection.keys():
    #         worksheet.write(row - 1, 5, 'Total On' + " " + str("(" + total + ")") + "Amount : ")
    #         worksheet.write(row - 1, 6, total_collection[total])
    #         row += 1
    #     row+=1
    #         # print(total)
    #         # print("total",total_collection[total])
    #
    #     row += 1
    #     workbook.close()
    #     out = base64.encodestring(fp.getvalue())
    #     self.write({'datas': out, 'datas_fname': filename})
    #     fp.close()
    #     filename += '%2Exlsx'
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'target': 'new',
    #         'url': 'web/content/?model=' + self._name + '&id=' + str(
    #             self.id) + '&field=datas&download=true&filename=' + filename,
    #     }
    # def add_workbook_format(self, workbook):
    #     colors = {
    #         'white_orange': '#FFFFDB',
    #         'orange': '#FFC300',
    #         'red': '#FF0000',
    #         'yellow': '#F6FA03',
    #     }
    #
    #     wbf = {}
    #     wbf['header'] = workbook.add_format(
    #         {'bold': 1, 'align': 'center', 'bg_color': '#FFFFDB', 'font_color': '#000000', 'font_name': 'Georgia'})
    #     wbf['header'].set_border()
    #
    #     wbf['header_orange'] = workbook.add_format(
    #         {'bold': 1, 'align': 'center', 'bg_color': colors['orange'], 'font_color': '#000000',
    #          'font_name': 'Georgia'})
    #     wbf['header_orange'].set_border()
    #
    #     wbf['header_yellow'] = workbook.add_format(
    #         {'bold': 1, 'align': 'center', 'bg_color': colors['yellow'], 'font_color': '#000000',
    #          'font_name': 'Georgia'})
    #     wbf['header_yellow'].set_border()
    #
    #     wbf['header_no'] = workbook.add_format(
    #         {'bold': 1, 'align': 'center', 'bg_color': '#FFFFDB', 'font_color': '#000000', 'font_name': 'Georgia'})
    #     wbf['header_no'].set_border()
    #     wbf['header_no'].set_align('vcenter')
    #
    #     wbf['footer'] = workbook.add_format({'align': 'left', 'font_name': 'Georgia'})
    #
    #     wbf['content_datetime'] = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss', 'font_name': 'Georgia'})
    #     wbf['content_datetime'].set_left()
    #     wbf['content_datetime'].set_right()
    #
    #     wbf['content_date'] = workbook.add_format({'num_format': 'yyyy-mm-dd', 'font_name': 'Georgia'})
    #     wbf['content_date'].set_left()
    #     wbf['content_date'].set_right()
    #
    #     wbf['title_doc'] = workbook.add_format({
    #         'bold': True,
    #         'align': 'center',
    #         'valign': 'vcenter',
    #         'font_size': 20,
    #         'font_name': 'Georgia',
    #     })
    #
    #     wbf['company'] = workbook.add_format({'align': 'left', 'font_name': 'Georgia'})
    #     wbf['company'].set_font_size(11)
    #
    #     wbf['content'] = workbook.add_format()
    #     wbf['content'].set_left()
    #     wbf['content'].set_right()
    #
    #     wbf['content_float'] = workbook.add_format(
    #         {'align': 'right', 'num_format': '#,##0.00', 'font_name': 'Georgia'})
    #     wbf['content_float'].set_right()
    #     wbf['content_float'].set_left()
    #
    #     wbf['content_number'] = workbook.add_format(
    #         {'align': 'right', 'num_format': '#,##0', 'font_name': 'Georgia'})
    #     wbf['content_number'].set_right()
    #     wbf['content_number'].set_left()
    #
    #     wbf['content_percent'] = workbook.add_format(
    #         {'align': 'right', 'num_format': '0.00%', 'font_name': 'Georgia'})
    #     wbf['content_percent'].set_right()
    #     wbf['content_percent'].set_left()
    #
    #     wbf['total_float'] = workbook.add_format(
    #         {'bold': 1, 'bg_color': colors['white_orange'], 'align': 'right', 'num_format': '#,##0.00',
    #          'font_name': 'Georgia'})
    #     wbf['total_float'].set_top()
    #     wbf['total_float'].set_bottom()
    #     wbf['total_float'].set_left()
    #     wbf['total_float'].set_right()
    #
    #     wbf['total_number'] = workbook.add_format(
    #         {'align': 'right', 'bg_color': colors['white_orange'], 'bold': 1, 'num_format': '#,##0',
    #          'font_name': 'Georgia'})
    #     wbf['total_number'].set_top()
    #     wbf['total_number'].set_bottom()
    #     wbf['total_number'].set_left()
    #     wbf['total_number'].set_right()
    #
    #     wbf['total'] = workbook.add_format(
    #         {'bold': 1, 'bg_color': colors['white_orange'], 'align': 'center', 'font_name': 'Georgia'})
    #     wbf['total'].set_left()
    #     wbf['total'].set_right()
    #     wbf['total'].set_top()
    #     wbf['total'].set_bottom()
    #
    #     wbf['total_float_yellow'] = workbook.add_format(
    #         {'bold': 1, 'bg_color': colors['yellow'], 'align': 'right', 'num_format': '#,##0.00',
    #          'font_name': 'Georgia'})
    #     wbf['total_float_yellow'].set_top()
    #     wbf['total_float_yellow'].set_bottom()
    #     wbf['total_float_yellow'].set_left()
    #     wbf['total_float_yellow'].set_right()
    #
    #     wbf['total_number_yellow'] = workbook.add_format(
    #         {'align': 'right', 'bg_color': colors['yellow'], 'bold': 1, 'num_format': '#,##0',
    #          'font_name': 'Georgia'})
    #     wbf['total_number_yellow'].set_top()
    #     wbf['total_number_yellow'].set_bottom()
    #     wbf['total_number_yellow'].set_left()
    #     wbf['total_number_yellow'].set_right()
    #
    #     wbf['total_yellow'] = workbook.add_format(
    #         {'bold': 1, 'bg_color': colors['yellow'], 'align': 'center', 'font_name': 'Georgia'})
    #     wbf['total_yellow'].set_left()
    #     wbf['total_yellow'].set_right()
    #     wbf['total_yellow'].set_top()
    #     wbf['total_yellow'].set_bottom()
    #
    #     wbf['total_float_orange'] = workbook.add_format(
    #         {'bold': 1, 'bg_color': colors['orange'], 'align': 'right', 'num_format': '#,##0.00',
    #          'font_name': 'Georgia'})
    #     wbf['total_float_orange'].set_top()
    #     wbf['total_float_orange'].set_bottom()
    #     wbf['total_float_orange'].set_left()
    #     wbf['total_float_orange'].set_right()
    #
    #     wbf['total_number_orange'] = workbook.add_format(
    #         {'align': 'right', 'bg_color': colors['orange'], 'bold': 1, 'num_format': '#,##0',
    #          'font_name': 'Georgia'})
    #     wbf['total_number_orange'].set_top()
    #     wbf['total_number_orange'].set_bottom()
    #     wbf['total_number_orange'].set_left()
    #     wbf['total_number_orange'].set_right()
    #
    #     wbf['total_orange'] = workbook.add_format(
    #         {'bold': 1, 'bg_color': colors['orange'], 'align': 'center', 'font_name': 'Georgia'})
    #     wbf['total_orange'].set_left()
    #     wbf['total_orange'].set_right()
    #     wbf['total_orange'].set_top()
    #     wbf['total_orange'].set_bottom()
    #
    #     wbf['header_detail_space'] = workbook.add_format({'font_name': 'Georgia'})
    #     wbf['header_detail_space'].set_left()
    #     wbf['header_detail_space'].set_right()
    #     wbf['header_detail_space'].set_top()
    #     wbf['header_detail_space'].set_bottom()
    #
    #     wbf['header_detail'] = workbook.add_format({'bg_color': '#E0FFC2', 'font_name': 'Georgia'})
    #     wbf['header_detail'].set_left()
    #     wbf['header_detail'].set_right()
    #     wbf['header_detail'].set_top()
    #     wbf['header_detail'].set_bottom()
    #
    #     return wbf, workbook
    # End of excel


    def get_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.date_start, 'date_end': self.date_end,'company_id':self.company_id.id, 'branch_id': self.branch_ids.id,
                'branch_name': self.branch_ids.name,'area':self.area.ids,
            },
        }
        print("data",data)

        # ref `module_name.report_id` as reference.
        return self.env.ref('sale_report.sales_area_wise_report').report_action(
            self, data=data)



class AreaWiseSalesReportView(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.sale_report.area_wise_sales_report_view'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        branch_id = data['form']['branch_id']
        branch_name = data['form']['branch_name']

        company_id=data['form']['company_id']
        area=data['form']['area']
        print("1starea",area)
        if branch_id:
            branch_id = " m.branch_id = %s" % branch_id

        else:
             branch_id = "1=1"

        if company_id:
            company_id = " m.company_id = %s" % company_id

        else:
             company_id = "1=1"

        # if area:
        #     area = " ca.id in %s" % area
        #     print("area2nd",area)
        # else:
        #     area = "1=1"
        get_area_ids = []
        where_area_ids = "1=1"
        if area:
            if area:
                print("area3rd",area)
                get_area_ids = " ca.id in %s" % str(tuple(area)).replace(',)', ')')  # create a tuple and remove comma
                # area = " ca.id in %s" % area
                print("area2nd", area)
            # for id in area:
            #     if id != "":
            #         get_area_ids.append(int(id))



        # if len(get_area_ids) == 1:
        #     where_area_ids = " ca.id = {}".format(get_area_ids[0])
        # if len(get_area_ids) > 1:
        #     where_area_ids = " ca.id in {}".format(tuple(get_area_ids))


        query = """select ca.area_name,p.name as customer,sum(l.credit) TotalSalesAmount from account_move m
                            left join account_move_line l on m.id=l.move_id
                            left join res_partner p on p.id=m.partner_id
                            inner join customer_area_setup ca on ca.id=p.customer_area
                            left join res_branch br on br.id=m.branch_id
                            where account_root_id=52048 and m.state='posted' and {} and m.date::date between '{}' and '{}' and {} and {} and m.company_id=br.company_id
                            group by ca.area_name,p.name
                            order by ca.area_name,p.name
                           """.format(branch_id, date_start, date_end, company_id,where_area_ids)

        self._cr.execute(query=query)
        query_result = self._cr.fetchall()
        print("query_result",query_result)
        area_sales = dict()

        for collection in query_result:

            print(collection[0])
            area = collection[0]
            if area not in area_sales.keys():
                area_sales[area] = dict()
            if collection[0] in area_sales[area].keys():
                area_sales[area].append(collection)
            else:
                area_sales[area] = list()
                area_sales[area].append(collection)
        print("area_sales",area_sales)
        print("collection", collection)
        return {
            'date_start': date_start,
            'date_end': date_end,
            'branch': branch_name,
            'area_sales': area_sales,
            # 'area': area,
        }
