# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, datetime, BytesIO, xlsxwriter, base64
from custom_module.accounting_report.models.usl_xlxs_report_tools import UslXlxsReportUtil as utill


class DishonorChequeReportWizard(models.TransientModel):
    _name = 'dishonor.report.wizard'

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    date_start = fields.Date(string='Start Dishonor Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Dishonor Date', required=True, default=fields.Date.today)
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self:self._get_companies(),default=lambda self: self.env.user.company_id,required=True)
    branch_ids = fields.Many2many('res.branch', 'dishonor_branch_report__rel',
                                  'dishonor_branch_id',
                                  'branch_id', 'Branches')
    customer_ids=fields.Many2many('res.partner','dishonor_partner_report_rel','dishonor_partner_id','partner_id','Customers', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    # customer_ids = fields.Many2one('res.partner', string='Partners',
    #                               domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", )
    # payment_method = fields.Many2one('account.payment.method', string='Payment Method')

    # # @api.onchange('branch_ids')
    # # def getCustomers(self):
    # #     query="""select """
    # @api.onchange("branch_ids")
    # def get_customers(self):
    #     if self.branch_ids.ids:
    #         customer_ids=self.env['sale.order'].search([('branch_id','in',self.branch_ids.ids)])
    #     else:
    #         customer_ids = self.env['sale.order'].search([])
    #     # query="""select partner_id from sale_order where branch_id in {}""".format(self.branch_ids.ids)
    #     # self._cr.execute(query=query)
    #     # customer_ids=self._cr.fetchall()
    #     print(self.branch_ids.ids)
    #     print(customer_ids.ids)
    #     return {"domain": {"customer_ids": [("id", "in", customer_ids.ids)]}}


    def _get_companies(self):
        query="""select * from res_company_users_rel where user_id={}""".format(self.env.user.id)
        self._cr.execute(query=query)
        allowed_companies=self._cr.fetchall()
        allowed_company=[]
        for company in allowed_companies:
            allowed_company.append(company[0])
        return  [('id', 'in', allowed_company)]





    def get_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.date_start, 'date_end': self.date_end,'company_id':self.company_id.id, 'branch_ids': self.branch_ids,
                'customer_ids':self.customer_ids,

            },
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('accounting_report.Cheque_dishonored_report').with_context(landscape=True).report_action(
            self, data=data)
    def get_excel_report(self):
        print('get_excel_report')
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.date_start, 'date_end': self.date_end, 'company_id': self.company_id.id,
                'branch_ids': self.branch_ids,
                'customer_ids': self.customer_ids,

            },
        }
        start_date = data['form']['date_start']
        end_date = data['form']['date_end']
        branch_ids = data['form']['branch_ids']
        customer_ids = data['form']['customer_ids']
        company_id = data['form']['company_id']
        # start_date = datetime.strptime(date_start, DATE_FORMAT)
        # end_date = datetime.strptime(date_end, DATE_FORMAT)
        where_branch_ids = "1=1"
        where_customer_ids = "1=1"
        if branch_ids:
            where_branch_ids = " ap.branch_id in %s" % str(tuple(branch_ids.ids)).replace(',)', ')')

        if customer_ids:
            where_customer_ids = "ap.partner_id in %s" % str(tuple(customer_ids.ids)).replace(',)', ')')

        query = """select rpp.name,rb.name,ap.cheque_reference,ap.payment_date::DATE, ap.effective_date::DATE ,bk.bank_name,ap.name,
                ap.dishonor_count,sp.name, ap.sent_date::DATE ,aj.name, ap.dishonor_date::DATE,ap.amount from account_payment ap
                left join res_partner rpp on rpp.id=ap.partner_id
                left join res_branch rb on rb.id=ap.branch_id
                left join res_partner customer on customer.id = ap.partner_id
				left join res_users ru on ru.id = customer.user_id
                left join res_partner sp on sp.id = ru.partner_id
                left join account_journal aj on aj.id=ap.journal_id 
                left join bank_info_all_bank bk on bk.id = ap.bank_id
                where ap.state='dishonored' and ap.dishonor_date::date between '{}'::date and '{}'::date and  {} and  {} and company_id_new = {}""".format(
            start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT), where_branch_ids,
            where_customer_ids, company_id)
        #
        # query = """select rpp.name,rb.name,ap.cheque_reference,to_char(ap.create_date,'DD-MON-YYYY'),to_char(ap.payment_date,'DD-MON-YYYY'),ap.bank_reference,ap.name,
        #                 ap.dishonor_count,rp.name,to_char(ap.sent_date,'DD-MON-YYYY'),aj.name,to_char(ap.honor_date,'DD-MON-YYYY'),ap.amount from account_payment ap
        #                 left join res_partner rpp on rpp.id=ap.partner_id
        #                 left join res_branch rb on rb.id=ap.branch_id
        #                 left join account_move am on am.name=ap.communication
        #                 left join res_partner rp on rp.id=am.create_uid
        #                 left join account_journal aj on aj.id=ap.journal_id
        #                 where ap.state='dishonored' and ap.dishonor_date::date between '{}' and '{}' and  {} and  {}""".format(
        #     start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT), where_branch_ids,
        #     where_customer_ids)
        self._cr.execute(query=query)
        dishonored_result = self._cr.fetchall()
        print(dishonored_result)

        dishonored_cheque = dict()
        for res in dishonored_result:
            if res[0] not in dishonored_cheque.keys():
                dishonored_cheque[res[0]] = list()
                dishonored_cheque[res[0]].append(res)
            else:
                # dishonored_cheque[res[0]] = list()
                dishonored_cheque[res[0]].append(res)
        report_name = 'Dishonor Cheque Report'
        filename = '%s' % (report_name)
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = utill.add_workbook_format(workbook=workbook)

        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:I3', report_name, wbf['title_doc'])

        cloumn_product = [
            ('Sl no', 5, 'float', 'no'),
            ('Branch', 30, 'char', 'float'),
            ('Cheque No', 15, 'char', 'float'),
            ('Rec. Date', 20, 'char', 'float'),
            ('Cheque Date', 20, 'char', 'float'),
            ('Bank Name', 15, 'char', 'float'),
            ('collection No.', 20, 'char', 'float'),
            ('Dishonor ', 20, 'float', 'float'),
            ('Sale Person ', 20, 'char', 'float'),
            ('Place Date ', 20, 'char', 'float'),
            ('Place Bank', 20, 'char', 'float'),
            ('H/D Date', 20, 'char', 'float'),
            ('Amount', 20, 'float', 'float'),

        ]
        row = 6

        grand_total = 0
        col = 0
        _row = 4
        for column in cloumn_product:
            column_name = column[0]
            column_width = column[1]
            worksheet.set_column(col, col, column_width)
            worksheet.write(_row, col, column_name, wbf['header_orange'])
            col += 1
        row += 2
        for group in dishonored_cheque.keys():
            worksheet.merge_range('A%s:M%s' % (row, row), str(group), wbf['header_orange'])
            # row += 1

            sl_no = 1
            sub_total = 0
            for data in dishonored_cheque[group]:
                worksheet.write(row, 0, sl_no)
                sl_no += 1
                clmn = 1
                for index, _ in enumerate(data, start=1):
                    if index > 12:
                        break
                    worksheet.write(row, clmn, data[index])
                    clmn += 1
                row += 1
                sub_total += data[12]
                grand_total += data[12]

            row += 1
            worksheet.merge_range('A%s:L%s' % (row, row), 'Sub Total :', wbf['header_orange'])
            worksheet.write(row - 1, 12, sub_total, wbf['header_orange'])
            row += 2

        worksheet.merge_range('A%s:L%s' % (row-1, row-1), 'Grand Total :', wbf['header_orange'])
        worksheet.write(row - 2, 12, grand_total, wbf['header_orange'])
        row += 2
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


class ReportSaleSummaryLocationWiseReportView(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.accounting_report.dishonored_cheque_report_view'

    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        branch_ids = data['form']['branch_ids']
        customer_ids = data['form']['customer_ids']
        company_id = data['form']['company_id']
        start_date = datetime.strptime(date_start, DATE_FORMAT)
        end_date = datetime.strptime(date_end, DATE_FORMAT)

        branch_id=eval(branch_ids.strip('res.branch'))

        if branch_id != ():
            branch_id = list(branch_id)
            branch_id.append(0)
            branch_id = tuple(branch_id)
        print(branch_id)
        where_branch_ids="1=1"
        where_customer_ids="1=1"
        if branch_id and branch_id!=():
            where_branch_ids="ap.branch_id in {}".format(branch_id)

        customer_id = eval(customer_ids.strip('res.partner'))

        if customer_id != ():
            customer_id = list(customer_id)
            customer_id.append(0)
            customer_id = tuple(customer_id)
        print(customer_id)

        if customer_id and customer_id!=():
            where_customer_ids="ap.partner_id in {}".format(customer_id)

        query="""select rpp.name,rb.name,ap.cheque_reference,ap.payment_date::DATE, ap.effective_date::DATE ,bk.bank_name,ap.name,
                ap.dishonor_count,sp.name, ap.sent_date::DATE ,aj.name, ap.dishonor_date::DATE,ap.amount from account_payment ap
                left join res_partner rpp on rpp.id=ap.partner_id
                left join res_branch rb on rb.id=ap.branch_id
                left join res_partner customer on customer.id = ap.partner_id
				left join res_users ru on ru.id = customer.user_id
                left join res_partner sp on sp.id = ru.partner_id
                left join account_journal aj on aj.id=ap.journal_id 
                left join bank_info_all_bank bk on bk.id = ap.bank_id
                where ap.state='dishonored' and ap.dishonor_date::date between '{}'::date and '{}'::date and  {} and  {} and company_id_new = {}""".format(
            start_date.strftime(DATETIME_FORMAT), end_date.strftime(DATETIME_FORMAT),where_branch_ids,where_customer_ids, company_id)
        self._cr.execute(query=query)
        dishonored_result=self._cr.fetchall()
        print(dishonored_result)

        dishonored_cheque=dict()
        for res in dishonored_result:
            if res[0] not in dishonored_cheque.keys():
                dishonored_cheque[res[0]]=list()
                dishonored_cheque[res[0]].append(res)
            else:
                dishonored_cheque[res[0]].append(res)

        print(dishonored_cheque)

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start,
            'date_end': date_end,
            # 'group_value':group_value,
            # 'products':products,
            # 'docs': self.env['account.move'].browse(docids),
            'dishonored_result': dishonored_cheque,


        }