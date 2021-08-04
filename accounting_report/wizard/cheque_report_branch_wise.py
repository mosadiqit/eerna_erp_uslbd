from datetime import datetime, timedelta
from odoo import models, fields
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, BytesIO, xlsxwriter, base64
from odoo import fields, models
from custom_module.accounting_report.models.usl_xlxs_report_tools import UslXlxsReportUtil as utill


class ChequeReportBranchWise(models.TransientModel):
    _name = "cheque.branchwise.report.wizard"
    _description = "Cheque report branch wise"

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

        bank_ids = data['bank_ids']
        start_date = data['start_date']
        end_date = data['end_date']
        company_ids = data['company_id']
        customer_ids = data['customer_ids']

        # start_date = start_date.strftime('%Y-%M-%D')
        print(type(start_date), end_date)
        where_company_ids = "1=1"
        where_customer_ids = "1=1"
        where_bank_ids = "1=1"

        # if location_ids:
        #     where_location_ids = " so.branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        # #     where_location_ids2 = " branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        # if group_ids:
        #     where_group_ids = " reg.group_id in %s" % str(tuple(group_ids)).replace(',)', ')')

        if bank_ids:
            where_bank_ids = " ap.branch_id in %s" % str(tuple(bank_ids)).replace(',)', ')')
        if company_ids:
            where_company_ids = " ap.company_id_new = {}".format(company_ids[0])
        if customer_ids:
            where_customer_ids = " ap.partner_id in %s" % str(tuple(customer_ids)).replace(',)', ')')

        query = """ 
                    select bk.bank_name,cheque_reference,effective_date,rp.name,bk.bank_name,'Send to Bank' as state,ap.sent_date::DATE,amount from account_payment as ap 
                    inner join res_partner as rp on ap.partner_id = rp.id 
					inner join bank_info_all_bank bk on bk.id = ap.bank_id
                    where {} and ap.state='waiting_for_approval' and ap.sent_date::DATE between '{}'::DATE and '{}'::DATE and {} and {}
                    """.format(where_bank_ids, start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT),
                               where_customer_ids, where_company_ids)

        # print(query)
        # print('print pdf report')
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
        return self.env.ref('accounting_report.branchwise_report').report_action(
            self, data=data)

    def get_excel_report(self):
        print('get_excel_report')
        data = self.read()[0]
        print('data : ',data)

        bank_ids = data['bank_ids']
        start_date = data['start_date']
        end_date = data['end_date']
        company_ids = data['company_id']
        customer_ids = data['customer_ids']

        # start_date = start_date.strftime('%Y-%M-%D')
        print(type(start_date), end_date)
        where_company_ids = "1=1"
        where_customer_ids = "1=1"
        where_bank_ids = "1=1"

        # if location_ids:
        #     where_location_ids = " so.branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        # #     where_location_ids2 = " branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')
        # if group_ids:
        #     where_group_ids = " reg.group_id in %s" % str(tuple(group_ids)).replace(',)', ')')

        if bank_ids:
            where_bank_ids = " ap.branch_id in %s" % str(tuple(bank_ids)).replace(',)', ')')
        if company_ids:
            where_company_ids = " ap.company_id_new = {}".format(company_ids[0])
        if customer_ids:
            where_customer_ids = " ap.partner_id in %s" % str(tuple(customer_ids)).replace(',)', ')')

        query = """ 
                    select bk.bank_name,cheque_reference,effective_date,rp.name,bk.bank_name,'Send to Bank' as state,ap.sent_date::DATE,amount from account_payment as ap
                    inner join res_partner as rp on ap.partner_id = rp.id 
					inner join bank_info_all_bank bk on bk.id = ap.bank_id
                    where {} and ap.state='waiting_for_approval' and ap.sent_date::DATE between '{}'::DATE and '{}'::DATE and {} and {}
                    """.format(where_bank_ids, start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT),
                               where_customer_ids, where_company_ids)

        # print(query)
        # print('print pdf report')
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

        if 'star_date' in data.keys():
            start_date = data['star_date']
        else:
            start_date = data['start_date']
        end_date = data['end_date']
        results = data['result']

        print('\n\n\n')

        buyer_dict = dict()
        for result in results:
            if result[0] not in buyer_dict.keys():  # result[0] is 'name' in account_journal(using for group_by)
                buyer_dict[result[
                    0]] = list()  # if the 'name' of account_journal is not in list then create and append all items of this account_journal(bank name)
                buyer_dict[result[0]].append(result)
            else:
                buyer_dict[result[0]].append(result)
        report_name = 'Cheque Send Report'
        filename = '%s' % (report_name)
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = utill.add_workbook_format(workbook=workbook)

        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:I3', report_name, wbf['title_doc'])

        cloumn_product = [
            ('Sl no', 10, 'float', 'no'),
            ('Cheque no', 15, 'char', 'float'),
            ('Cheque Date', 20, 'char', 'float'),
            ('Buyer Name', 39, 'char', 'float'),
            ('Bank Name', 39, 'char', 'float'),
            ('status', 15, 'char', 'float'),
            ('Pending Date', 20, 'char', 'float'),
            ('Amount', 20, 'float', 'float'),

        ]
        row = 6

        grand_total = 0
        for group in buyer_dict.keys():
            worksheet.merge_range('A%s:H%s' % (row, row), 'Bank :' + str(group), wbf['header_orange'])
            row += 1
            col = 0
            for column in cloumn_product:
                column_name = column[0]
                column_width = column[1]
                worksheet.set_column(col, col, column_width)
                worksheet.write(row, col, column_name, wbf['header_orange'])
                col += 1
            row += 1
            sl_no = 1
            sub_total = 0
            for data in buyer_dict[group]:
                worksheet.write(row, 0, sl_no)
                worksheet.write(row, 1, data[1])
                worksheet.write(row, 2, str(data[2]))
                worksheet.write(row, 3, data[3])
                worksheet.write(row, 4, data[4])
                worksheet.write(row, 5, data[5])
                worksheet.write(row, 6, str(data[6]))
                worksheet.write(row, 7, data[7])
                sub_total += data[7]
                grand_total += data[7]
                sl_no += 1
                row += 1
            row += 1
            worksheet.merge_range('A%s:G%s' % (row, row), 'Sub Total :', wbf['header_orange'])
            worksheet.write(row-1, 7, sub_total,wbf['header_orange'])
            row += 1

        worksheet.merge_range('A%s:G%s' % (row, row), 'Grand Total :', wbf['header_orange'])
        worksheet.write(row-1, 7, grand_total, wbf['header_orange'])
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

    start_date = fields.Date(string="Start Send Date", default=datetime.now())
    end_date = fields.Date(string='End Send Date', default=datetime.now())
    customer_ids = fields.Many2many('res.partner', string='Customer')
    bank_ids = fields.Many2many('res.branch', string='Branch')
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),
                                 default=lambda self: self.env.user.company_id, required=True)


class ChequeReportBranchWiseModel(models.AbstractModel):
    _name = 'report.accounting_report.cheque_report_branch_wise'

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
        for result in results:
            if result[0] not in buyer_dict.keys():  # result[0] is 'name' in account_journal(using for group_by)
                buyer_dict[result[
                    0]] = list()  # if the 'name' of account_journal is not in list then create and append all items of this account_journal(bank name)
                buyer_dict[result[0]].append(result)
            else:
                buyer_dict[result[0]].append(result)
        print(buyer_dict)

        return {
            'group_value': results,
            'start_date': start_date,
            'end_date': end_date,
            'data': buyer_dict,
        }


'''

select aj.name,cheque_reference,payment_date,rp.name,bank_reference,state,effective_date,amount from account_payment as ap 
left join res_partner as rp on ap.partner_id = rp.id 
left join account_journal as aj on ap.journal_id=aj.id
where ap.state='sent' 
'''
