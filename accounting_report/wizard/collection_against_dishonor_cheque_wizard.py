from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, BytesIO, xlsxwriter, base64
from odoo import fields, models
from custom_module.accounting_report.models.usl_xlxs_report_tools import UslXlxsReportUtil as utill
import datetime as dt


class CollectionAgainstDishonorCheque(models.TransientModel):
    _name = 'accounting.collection_against_dishonor_cheque.wizard'
    _description = 'CollectionAgainstDishonorCheque'

    def get_report(self):
        # data = self.read()[0]
        # print(data)
        # where_customer_ids = "1=1"
        # where_branch_ids = "1=1"
        # where_company_id = "1=1"
        # start_date = data.get('start_date')
        # end_date = data.get('end_date')
        # branch_ids = data.get('branch_ids')
        # customer = data.get('customer')
        # company_id = data.get('company_id')
        # if branch_ids:
        #     where_branch_ids = " ap.branch_id in %s" % str(tuple(branch_ids)).replace(',)', ')')
        # if customer:
        #     where_customer_ids = " ap.partner_id in %s" % str(tuple(customer)).replace(',)', ')')
        # if company_id:
        #     where_company_id = " rb.company_id = {}".format(company_id[0])
        #
        # query = """select rb.name as branch, rp.name as customer,ap.bank_reference,ap.check_number,ap.payment_date,ap.effective_date,ap.amount from account_payment as ap
        #     left join res_partner as rp on ap.partner_id = rp.id
        #     left join res_branch as rb on ap.branch_id=rb.id
        #     where ap.state = 'posted' and ap.dishonor_count >0 and ap.payment_date between '{}'and '{}' and {} and {} and {}""".format(
        #     start_date, end_date, where_customer_ids, where_branch_ids, where_company_id)
        # self._cr.execute(query)
        # result = self._cr.fetchall()
        # print(result)
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.start_date, 'date_end': self.end_date, 'company_id': self.company_id.id,
                'branch_ids': self.branch_ids,
                'customer_ids': self.customer,

            },
        }
        return self.env.ref('accounting_report.collection_against_dishonor_cheque').report_action(
            self, data=data)

    def get_excel_report(self):
        data = self.read()[0]
        where_customer_ids = "1=1"
        where_branch_ids = "1=1"
        where_company_id = "1=1"
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        branch_ids = data.get('branch_ids')
        customer = data.get('customer')
        company_id = data.get('company_id')
        if branch_ids:
            where_branch_ids = " ap.branch_id in %s" % str(tuple(branch_ids)).replace(',)', ')')
        if customer:
            where_customer_ids = " ap.partner_id in %s" % str(tuple(customer)).replace(',)', ')')
        if company_id:
            where_company_id = " ap.company_id_new = {}".format(company_id[0])

        query = """select br.name as branch_name, pr.name as partner_name, b.bank_name as bank_name, ap.cheque_reference, ap.payment_date, ap.effective_date, ap.amount, 
                        COALESCE(ap.dishonor_balance_adjust_amt, 0), ap.amount - COALESCE(ap.dishonor_balance_adjust_amt, 0) as balance
                        from account_payment ap
                        inner join bank_info_all_bank b on b.id = ap.bank_id
                        inner join res_branch br on br.id = ap.branch_id
                        inner join res_partner pr on pr.id = ap.partner_id
                        where ap.state='dishonored' and ap.dishonor_date::date between '{}' and '{}' and  {} and  {} and {}""".format(
            start_date, end_date, where_customer_ids, where_branch_ids, where_company_id)
        self._cr.execute(query)
        result = self._cr.fetchall()
        dic_data = dict()
        brand_dic = dict()

        for reslt in result:
            # print(reslt[3])
            if reslt[0] not in dic_data.keys():
                dic_data[reslt[0]] = dict()
            if reslt[1] not in dic_data[reslt[0]].keys():
                brand_dic[reslt[0]] = set()
                brand_dic[reslt[0]].add(reslt[1])
                dic_data[reslt[0]][reslt[1]] = list()
                dic_data[reslt[0]][reslt[1]].append(reslt)
            else:
                brand_dic[reslt[0]].add(reslt[1])
                dic_data[reslt[0]][reslt[1]].append(reslt)

        report_name = 'Collection Against Dishonor Cheque'
        filename = '%s' % (report_name)
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = utill.add_workbook_format(workbook=workbook)

        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:G2', report_name, wbf['title_doc'])

        cloumn_product = [
            ('BankName', 10, 'char', 'no'),
            ('ChequeNo', 15, 'char', 'float'),
            ('RecDate', 20, 'char', 'float'),
            ('ChequeDate', 39, 'char', 'float'),
            ('ChequeAmount', 20, 'char', 'float'),

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
        row += 2
        grand_total = 0
        for product in dic_data.keys():

            worksheet.merge_range('A%s:E%s' % (row, row), product, wbf['total_orange'])
            row += 1
            first_group_total = 0
            for second_goup in dic_data[product].keys():
                second_goup_total = 0
                worksheet.merge_range('A%s:E%s' % (row, row), second_goup, wbf['total_orange'])
                for cheque in dic_data[product][second_goup]:
                    coll = 0
                    for index, column in enumerate(cheque, start=2):
                        if index > 6:
                            break
                        # print(type(cheque[index]))
                        if isinstance(cheque[index], dt.date):
                            print('come date time')
                            collm = str(cheque[index])
                            worksheet.write(row, coll, collm)
                        else:
                            worksheet.write(row, coll, cheque[index])

                        coll += 1
                    row += 1
                    grand_total += cheque[6]
                    first_group_total += cheque[6]
                    second_goup_total += cheque[6]
                row += 1
                worksheet.merge_range('A%s:D%s' % (row, row), 'Buyer Subtotal ', wbf['total_orange'])
                worksheet.write(row - 1, 4, second_goup_total, wbf['total_orange'])
                row += 1
            worksheet.merge_range('A%s:D%s' % (row, row), 'Branch Subtotal ', wbf['total_orange'])
            worksheet.write(row - 1, 4, first_group_total, wbf['total_orange'])
            row += 1
        worksheet.merge_range('A%s:D%s' % (row, row), 'Grand Total ', wbf['total_orange'])
        worksheet.write(row - 1, 4, grand_total, wbf['total_orange'])
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

    def _get_companies(self):
        query = """select * from res_company_users_rel where user_id={}""".format(self.env.user.id)
        self._cr.execute(query=query)
        allowed_companies = self._cr.fetchall()
        allowed_company = []
        for company in allowed_companies:
            allowed_company.append(company[0])
        return [('id', 'in', allowed_company)]

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    start_date = fields.Date(string='Start Dishonor Date', default=datetime.now())
    end_date = fields.Date(string='End Dishonor Date', default=datetime.now())
    branch_ids = fields.Many2many('res.branch', 'collection_dishonor_branch_rel',
                                  'dishonor_branch_id',
                                  'branch_id', string='Branches')
    customer = fields.Many2many('res.partner', 'res_partner_and_collection_ag_dis_che_rel', 'dishonor_partner_id',
                                'customer_id', string='Customer')
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),
                                 default=lambda self: self.env.user.company_id, required=True)

class CollectionAgainstDishonorChequeReport(models.AbstractModel):
    _name = 'report.accounting_report.collection_dishonor_cheque_template'

    def _get_report_values(self, docids, data=None):

        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        branch_ids = data['form']['branch_ids']
        customer_ids = data['form']['customer_ids']
        company_id = data['form']['company_id']
        start_date = datetime.strptime(date_start, DATE_FORMAT)
        end_date = datetime.strptime(date_end, DATE_FORMAT)

        branch_id = eval(branch_ids.strip('res.branch'))
        where_branch_ids = "1=1"
        where_customer_ids = "1=1"
        if branch_id and branch_id != ():
            where_branch_ids = "ap.branch_id in {}".format(branch_id)
        if company_id:
            where_company_id = " ap.company_id_new = {}".format(company_id)

        customer_id = eval(customer_ids.strip('res.partner'))

        if customer_id != ():
            customer_id = list(customer_id)
            customer_id.append(0)
            customer_id = tuple(customer_id)
        print(customer_id)

        if customer_id and customer_id != ():
            where_customer_ids = "ap.partner_id in {}".format(customer_id)
        query = """select br.name as branch_name, pr.name as partner_name, b.bank_name as bank_name, ap.cheque_reference, ap.payment_date, ap.effective_date, ap.amount, 
                        COALESCE(ap.dishonor_balance_adjust_amt, 0), ap.amount - COALESCE(ap.dishonor_balance_adjust_amt, 0) as balance
                        from account_payment ap
                        inner join bank_info_all_bank b on b.id = ap.bank_id
                        inner join res_branch br on br.id = ap.branch_id
                        inner join res_partner pr on pr.id = ap.partner_id
                        where ap.state='dishonored' and ap.dishonor_date::date between '{}' and '{}' and  {} and  {} and {}""".format(
            start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT), where_branch_ids,
            where_customer_ids, where_company_id)
        self._cr.execute(query=query)
        collection_agnst_dishonor_result = self._cr.fetchall()

        dic_data = dict()
        brand_dic = dict()
        for reslt in collection_agnst_dishonor_result:
            if reslt[0] not in dic_data.keys():
                dic_data[reslt[0]] = dict()
            if reslt[1] not in dic_data[reslt[0]].keys():
                brand_dic[reslt[0]] = set()
                brand_dic[reslt[0]].add(reslt[1])
                dic_data[reslt[0]][reslt[1]] = list()
                dic_data[reslt[0]][reslt[1]].append(reslt)
            else:
                brand_dic[reslt[0]].add(reslt[1])
                dic_data[reslt[0]][reslt[1]].append(reslt)

        return {
            'groups': list(brand_dic.keys()),
            'brands': brand_dic,
            'data': dic_data,
            'start_date': start_date,
            'end_date': end_date

        }
