
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, BytesIO, xlsxwriter, base64
from odoo import fields, models
from custom_module.accounting_report.models.usl_xlxs_report_tools import UslXlxsReportUtil as utill
import datetime


class ChequeInHandReport(models.TransientModel):
    _name = "cheque.in.hand.report.wizard"
    _description = "Cheque in hand report"

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
        data = self.read()[0]

        start_date = data['start_date']
        end_date = data['end_date']
        company_ids = data['company_id']
        customer_ids = data['customer_ids']
        # buyer_category = data['buyer_category']
        location_ids = data['location_ids']
        # start_date = start_date.strftime('%Y-%M-%D')
        print(type(start_date), end_date)
        where_company_ids = "1=1"
        where_customer_ids = "1=1"
        # where_buyer_category = "1=1"

        where_branch_ids = "1=1"

        # if location_ids:
        #     where_location_ids = " so.branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        # #     where_location_ids2 = " branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        # if group_ids:
        #     where_group_ids = " reg.group_id in %s" % str(tuple(group_ids)).replace(',)', ')')

        # if buyer_category:
        #     where_buyer_category = " ap.partner_type in %s" % str(tuple(buyer_category)).replace(',)', ')')
        if company_ids:
            where_company_ids = " ap.company_id_new = {}".format(company_ids[0])
        if customer_ids:
            where_customer_ids = " ap.partner_id in %s" % str(tuple(customer_ids)).replace(',)', ')')
        if location_ids:
            where_branch_ids = " ap.branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')

        query = """ select ap.partner_type,rp.name as partner_name,ap.cheque_reference,ap.cih_date as payment_date,ap.effective_date,bk.bank_name,ap.state,
                    ap.honor_date::DATE,amount,rb.name from account_payment ap 
					inner join res_partner rp on ap.partner_id=rp.id
                    inner join res_branch rb on ap.branch_id = rb.id
					inner join bank_info_all_bank bk on bk.id = ap.bank_id
                    where ap.cih_date::DATE between '{}'::DATE and '{}'::DATE and {} and {} and {} and ap.state='draft' AND (initial_create_status is null or initial_create_status = false)
                    """.format(start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT),
                               where_customer_ids, where_company_ids, where_branch_ids)

        print(query)
        print('print pdf report')
        self._cr.execute(query)
        result = self._cr.fetchall()
        # result = []
        # for i in results:
        #     result.append(i)

        print(result)
        data = {
            'result': result,
            'start_date': start_date,
            'end_date': end_date
        }
        return self.env.ref('accounting_report.in_hand_report').report_action(
            self, data=data)

    def get_excel_report(self):
        data = self.read()[0]

        start_date = data['start_date']
        end_date = data['end_date']
        company_ids = data['company_id']
        customer_ids = data['customer_ids']
        # buyer_category = data['buyer_category']
        location_ids = data['location_ids']
        # start_date = start_date.strftime('%Y-%M-%D')
        print(type(start_date), end_date)
        where_company_ids = "1=1"
        where_customer_ids = "1=1"
        # where_buyer_category = "1=1"
        where_branch_ids = "1=1"
        if company_ids:
            where_company_ids = " ap.company_id_new = {}".format(company_ids[0])
        if customer_ids:
            where_customer_ids = " ap.partner_id in %s" % str(tuple(customer_ids)).replace(',)', ')')
        if location_ids:
            where_branch_ids = " ap.branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        query = """ 
                            select ap.partner_type,rp.name as partner_name,ap.cheque_reference,ap.cih_date as payment_date,ap.effective_date,bk.bank_name,ap.state,
                            ap.honor_date::DATE,amount,rb.name from account_payment ap 
                            inner join res_partner rp on ap.partner_id=rp.id
                            inner join res_branch rb on ap.branch_id = rb.id
                            inner join bank_info_all_bank bk on bk.id = ap.bank_id
                            where ap.cih_date::DATE between '{}'::DATE and '{}'::DATE and {} and {} and {} and ap.state='draft' AND (initial_create_status is null or initial_create_status = false)
                            """.format(start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT),
                                       where_customer_ids, where_company_ids, where_branch_ids)

        print(query)
        print('print pdf report')
        self._cr.execute(query)
        result = self._cr.fetchall()
        data = {
            'result': result,
            'start_date': start_date,
            'end_date': end_date
        }
        if 'star_date' in data.keys():
            start_date = data['star_date']
        else:
            start_date = data['start_date']
        end_date = data['end_date']
        results = data['result']

        print('\n\n\n')

        buyer_dict = dict()

        for reslt in data['result']:
            if reslt[
                0] not in buyer_dict.keys():  # for the first time for vendor/production etc create a dictionary by creating a key which is 'buyer_group'
                buyer_dict[reslt[0]] = dict()  # create a new dictionary inside current dictionary in this index
            if reslt[1] not in buyer_dict[reslt[
                0]].keys():  # check this item inside the dictionary of dictionary,then create a list inside the dictionary of dictionary
                buyer_dict[reslt[0]][reslt[1]] = list()
                buyer_dict[reslt[0]][reslt[1]].append(
                    reslt)  # append items inside the list under the dictionary of dictionary
            else:
                buyer_dict[reslt[0]][reslt[1]].append(reslt)  # if the dictionary and list already created on this

        report_name = 'Cheque In Hand Report'
        filename = '%s' % (report_name)
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = utill.add_workbook_format(workbook=workbook)

        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:I3', report_name, wbf['title_doc'])

        cloumn_product = [
            ('Cheque No', 10, 'char', 'no'),
            ('Date', 15, 'char', 'float'),
            ('Cheque Date', 20, 'char', 'float'),
            ('Bank Name', 39, 'char', 'float'),
            ('State', 20, 'char', 'float'),
            ('Honor Date', 29, 'char', 'float'),
            ('Cheque Amount', 29, 'char', 'float'),

        ]
        row = 6
        col = 0
        for column in cloumn_product:
            column_name = column[0]
            column_width = column[1]
            column_type = column[2]
            worksheet.set_column(col, col, column_width)
            worksheet.write(row, col, column_name, wbf['header_orange'])
            col += 1
        row += 1
        grand_total = 0
        for product in buyer_dict.keys():
            worksheet.merge_range('A%s:G%s' % (row, row), product, wbf['total_orange'])
            row += 1
            first_group_total = 0
            for second_goup in buyer_dict[product].keys():
                second_goup_total = 0
                worksheet.merge_range('A%s:G%s' % (row, row), second_goup, wbf['total_orange'])
                row += 1
                for cheque in buyer_dict[product][second_goup]:
                    coll = 0
                    for index, column in enumerate(cheque, start=2):
                        if index > 8:
                            break
                        # print(type(cheque[index]))
                        if isinstance(cheque[index], datetime.date):
                            print('come date time')
                            collm = str(cheque[index])
                            worksheet.write(row, coll, collm, wbf['header_orange'])
                        else:
                            worksheet.write(row, coll, cheque[index], wbf['header_orange'])

                        coll += 1
                    row += 1
                    grand_total += cheque[8]
                    first_group_total += cheque[8]
                    second_goup_total += cheque[8]
                row += 1
                worksheet.merge_range('A%s:F%s' % (row, row), 'Customer Group Subtotal ', wbf['total_orange'])
                worksheet.write(row - 1, 6, second_goup_total, wbf['total_orange'])
                row += 1
            worksheet.merge_range('A%s:F%s' % (row, row), 'Buyer Group Subtotal ', wbf['total_orange'])
            worksheet.write(row - 1, 6, first_group_total, wbf['total_orange'])
            row += 1
        worksheet.merge_range('A%s:F%s' % (row, row), 'Grand Total ', wbf['total_orange'])
        worksheet.write(row - 1, 6, grand_total, wbf['total_orange'])
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

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    start_date = fields.Date(string="Start Batch Approve Date", default=datetime.datetime.now())
    end_date = fields.Date(string='End Batch Approve Date', default=datetime.datetime.now())
    customer_ids = fields.Many2many('res.partner', string='Customer')
    # buyer_category = fields.Many2many('account.payment', string='Buyer Categories') # this field is using for wizard
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),
                                 default=lambda self: self.env.user.company_id, required=True)

    location_ids = fields.Many2many('res.branch', string='Branch')


class ChequeInHandReportModel(models.AbstractModel):
    _name = 'report.accounting_report.cheque_in_hand_report'

    def _get_report_values(self, docids, data=None):
        print(' work here ')
        if 'star_date' in data.keys():
            start_date = data['star_date']
        else:
            start_date = data['start_date']
        end_date = data['end_date']
        results = data['result']

        print('\n\n\n')

        buyer_dict = dict()

        for reslt in data['result']:
            if reslt[
                0] not in buyer_dict.keys():  # for the first time for vendor/production etc create a dictionary by creating a key which is 'buyer_group'
                buyer_dict[reslt[0]] = dict()  # create a new dictionary inside current dictionary in this index
            if reslt[1] not in buyer_dict[reslt[
                0]].keys():  # check this item inside the dictionary of dictionary,then create a list inside the dictionary of dictionary
                buyer_dict[reslt[0]][reslt[1]] = list()
                buyer_dict[reslt[0]][reslt[1]].append(
                    reslt)  # append items inside the list under the dictionary of dictionary
            else:
                buyer_dict[reslt[0]][reslt[1]].append(reslt)  # if the dictionary and list already created on this

        print(buyer_dict)
        return {
            'group_value': results,
            'start_date': start_date,
            'end_date': end_date,
            'data': buyer_dict,
        }
