# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, BytesIO, xlsxwriter, base64


class CollectionStatementReportWizard(models.TransientModel):
    _name = 'accounting.summary.report.wizard'

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Date', required=True, default=fields.Date.today)
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),
                                 default=lambda self: self.env.user.company_id, required=True)
    branch_ids = fields.Many2one('res.branch', string='Branch')
    payment_method = fields.Many2one('account.payment.method', string='Payment Method')

    def _get_companies(self):
        query = """select * from res_company_users_rel where user_id={}""".format(self.env.user.id)
        self._cr.execute(query=query)
        allowed_companies = self._cr.fetchall()
        allowed_company = []
        for company in allowed_companies:
            allowed_company.append(company[0])
        return [('id', 'in', allowed_company)]

    def print_excel_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.date_start, 'date_end': self.date_end, 'company_id': self.company_id.id,
                'branch_id': self.branch_ids.id,
                'branch_name': self.branch_ids.name, 'payment_method': self.payment_method.id,
            },
        }
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        branch_id = data['form']['branch_id']
        branch_name = data['form']['branch_name']
        payment_method = data['form']['payment_method']
        company_id = data['form']['company_id']

        if payment_method:
            payment_method = " ap.payment_method_id  = %s" % payment_method
        else:
            payment_method = "1=1"

        if branch_id:
            branch_id = " ap.branch_id = %s" % branch_id

        else:
            branch_id = "1=1"

        if company_id:
            company_id = " am.company_id = %s" % company_id

        else:
            company_id = "1=1"

        query = """
                   select distinct ap.payment_date::DATE payment_date, aj.name as payment_type, pm.name as paymentMethod, res_p.name as buyer, sp.name as sales_person, bp.name as money_recipt, collector.name as collected_by, ap.communication as invoice_no, ap.amount as collected_amount,ap.branch_id,br.name as branch_name 
            from account_payment ap 
            left join account_move am  on ap.move_name = am.name and am.state='posted'
            left join batch_payment bp on bp.id = ap.batch_payment_id
            left join res_partner collector on collector.id = bp.collected_by
            left join res_partner res_p on am.partner_id = res_p.id
            left join account_journal aj on ap.journal_id = aj.id
            left join account_payment_method pm on ap.payment_method_id = pm.id
            left join res_partner sp on sp.id = res_p.user_id
            left join res_branch br on br.id=ap.branch_id
            where ap.payment_type = 'inbound' and ap.state='posted' and ap.partner_type <> 'supplier' and {} and ap.payment_date::date between '{}' and '{}' and {} and {} and am.company_id=br.company_id
             ORDER BY payment_date, br.name, aj.name, pm.name, res_p.name, ap.communication, ap.amount,ap.branch_id
                   """.format(branch_id, date_start, date_end, payment_method, company_id)

        self._cr.execute(query=query)
        query_result = self._cr.fetchall()
        collection_statements = dict()
        for collection in query_result:
            print(collection[10])
            print(collection[0])
            collection_date = collection[0]
            if collection_date not in collection_statements.keys():
                collection_statements[collection_date] = dict()
            if collection[10] not in collection_statements[collection_date].keys():
                collection_statements[collection_date][collection[10]] = dict()
            if collection[2] not in collection_statements[collection_date][collection[10]].keys():
                collection_statements[collection_date][collection[10]][collection[2]] = dict()
            if collection[1] in collection_statements[collection_date][collection[10]][collection[2]].keys():
                collection_statements[collection_date][collection[10]][collection[2]][collection[1]].append(collection)
            else:
                collection_statements[collection_date][collection[10]][collection[2]][collection[1]] = list()
                collection_statements[collection_date][collection[10]][collection[2]][collection[1]].append(collection)

        total_collection = dict()
        date_wise_payment_method = dict()
        branch_wise_payment_method = dict()

        for single_collection in query_result:
            if single_collection[10] not in branch_wise_payment_method.keys():
                branch_wise_payment_method[single_collection[10]] = dict()

            if collection_date not in branch_wise_payment_method[single_collection[10]].keys():
                branch_wise_payment_method[single_collection[10]][collection_date] = dict()

            if single_collection[2] not in branch_wise_payment_method[single_collection[10]][collection_date].keys():
                branch_wise_payment_method[single_collection[10]][collection_date][single_collection[2]] = \
                    single_collection[-3]
            else:
                branch_wise_payment_method[single_collection[10]][collection_date][single_collection[2]] += \
                    single_collection[-3]

            # # Date wise payment
            # br_name = str(single_collection[10])
            if collection_date not in date_wise_payment_method.keys():
                date_wise_payment_method[collection_date] = dict()
            if single_collection[2] not in date_wise_payment_method[collection_date].keys():
                date_wise_payment_method[collection_date][single_collection[2]] = single_collection[-3]
            else:
                date_wise_payment_method[collection_date][single_collection[2]] += single_collection[-3]

            # total payment
            if single_collection[2] not in total_collection.keys():
                total_collection[single_collection[2]] = single_collection[-3]
            else:
                total_collection[single_collection[2]] += single_collection[-3]

        print(date_wise_payment_method)
        report_name = 'Collection Statement'
        filename = '%s' % (report_name)
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)
        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:D3', report_name, wbf['title_doc'])
        columns_group = [
            ('SL', 20, 'no', 'no'),
            ('Buyer', 20, 'char', 'char'),
            ('Sales Person', 30, 'char', 'char'),
            ('Money Receipt No', 30, 'char', 'char'),
            ('Collected By', 30, 'char', 'char'),
            ('Invoice No', 30, 'char', 'char'),
            ('Collected Amount', 30, 'char', 'char'),
        ]
        col = 0
        row = 4

        for group in columns_group:
            # col=0
            column_name1 = group[0]
            column_width = group[1]
            column_type = group[2]
            worksheet.set_column(col, col, column_width)
            worksheet.write(row - 1, col, column_name1, wbf['header_orange'])
            # worksheet.merge_range('A2:I3', column_name, wbf['header_orange'])
            col += 1
            # row += 1

        row += 1
        for date_group in collection_statements.keys():
            worksheet.merge_range('A%s:G%s' % (row, row), str(date_group), wbf['header_orange'])
            row += 1
            # col1 = 0
            print("date_group:", date_group)
            subtotal_date_wise = 0
            for branch in collection_statements[date_group]:
                worksheet.merge_range('A%s:G%s' % (row, row), str(branch), wbf['header_orange'])
                row += 1
                # col1 = 0
                print("branch:", branch)
                b_subtotal_tt_wise = b_subtotal_Checks_wise = b_subtotal_PDC_wise = b_subtotal_Electronic_wise = b_subtotal_Cash_wise = 0

                subtotal_branch_wise = 0
                for type in collection_statements[date_group][branch]:
                    worksheet.merge_range('A%s:G%s' % (row, row), str(type), wbf['header_orange'])
                    row += 1
                    # col1 = 0
                    print("type:", type)
                    subtotal_type_wise = 0
                    # subtotal_bank_wise=0
                    for bank in collection_statements[date_group][branch][type]:
                        worksheet.merge_range('A%s:G%s' % (row, row), str(bank), wbf['header_orange'])
                        row += 1
                        # col1 = 0
                        print("bank:", bank)
                        sl = 1
                        subtotal_bank_wise = 0
                        for collection in collection_statements[date_group][branch][type][bank]:
                            col2 = 0
                            worksheet.write(row - 1, col2, sl)
                            sl += 1
                            col2 += 1
                            worksheet.write(row - 1, col2, collection[3])
                            col2 += 1
                            worksheet.write(row - 1, col2, collection[4])
                            col2 += 1
                            worksheet.write(row - 1, col2, collection[5])
                            col2 += 1
                            worksheet.write(row - 1, col2, collection[6])
                            col2 += 1
                            worksheet.write(row - 1, col2, collection[7])
                            col2 += 1
                            worksheet.write(row - 1, col2, collection[8])
                            row += 1
                            print("collection:", collection)
                            subtotal_bank_wise += collection[8]
                            subtotal_type_wise += collection[8]
                            subtotal_branch_wise += collection[8]
                            subtotal_date_wise += collection[8]
                        print("subtotal_bank_wise", subtotal_bank_wise)
                        row += 1

                        worksheet.write(row - 1, 5, 'Sub Total of' + " " + str(bank) + " : ")
                        worksheet.write(row - 1, 6, subtotal_bank_wise)
                        row += 1
                    # b_subtotal_bank_wise=subtotal_bank_wise
                    if type == "TT":
                        b_subtotal_tt_wise = subtotal_type_wise
                    if type == "Checks":
                        b_subtotal_Checks_wise = subtotal_type_wise
                    if type == "PDC":
                        b_subtotal_PDC_wise = subtotal_type_wise
                    if type == "Electronic":
                        b_subtotal_Electronic_wise = subtotal_type_wise
                    if type == "Cash":
                        b_subtotal_Cash_wise = subtotal_type_wise
                    worksheet.write(row - 1, 5, 'Total' + " " + str(type) + " " + "Amount : ")
                    worksheet.write(row - 1, 6, subtotal_type_wise)
                    row += 1

                worksheet.merge_range('A%s:G%s' % (row, row), "Total On" + " " + str(branch), wbf['title_doc'])
                row += 1
                if b_subtotal_tt_wise > 0:
                    worksheet.write(row - 1, 5, 'Total TT Amount:')
                    worksheet.write(row - 1, 6, b_subtotal_tt_wise)
                    row += 1
                if b_subtotal_Checks_wise > 0:
                    worksheet.write(row - 1, 5, 'Total Cheque Amount:')
                    worksheet.write(row - 1, 6, b_subtotal_Checks_wise)
                    row += 1
                if b_subtotal_PDC_wise > 0:
                    worksheet.write(row - 1, 5, 'Total PDC Amount:')
                    worksheet.write(row - 1, 6, b_subtotal_PDC_wise)
                    row += 1
                if b_subtotal_Electronic_wise > 0:
                    worksheet.write(row - 1, 5, 'Total Electronic Amount:')
                    worksheet.write(row - 1, 6, b_subtotal_Electronic_wise)
                    row += 1
                if b_subtotal_Cash_wise > 0:
                    worksheet.write(row - 1, 5, 'Total Cash Amount:')
                    worksheet.write(row - 1, 6, b_subtotal_Cash_wise)
                    row += 1

                worksheet.write(row - 1, 5, 'Total Amount On' + " " + str(branch) + " : ")
                worksheet.write(row - 1, 6, subtotal_branch_wise)
                row += 2
            worksheet.merge_range('A%s:G%s' % (row, row), "Total Of" + " " + str(date_group), wbf['title_doc'])
            row += 1
            worksheet.write(row - 1, 5, 'Total Amount On' + " " + str("(" + date_group + ")") + " : ")
            worksheet.write(row - 1, 6, subtotal_date_wise)
            row += 2
        worksheet.merge_range('A%s:G%s' % (row, row), "Grand Total", wbf['title_doc'])
        row += 1
        for total in total_collection.keys():
            worksheet.write(row - 1, 5, 'Total On' + " " + str("(" + total + ")") + "Amount : ")
            worksheet.write(row - 1, 6, total_collection[total])
            row += 1
        row += 1
        # print(total)
        # print("total",total_collection[total])

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

        wbf['content_float'] = workbook.add_format(
            {'align': 'right', 'num_format': '#,##0.00', 'font_name': 'Georgia'})
        wbf['content_float'].set_right()
        wbf['content_float'].set_left()

        wbf['content_number'] = workbook.add_format(
            {'align': 'right', 'num_format': '#,##0', 'font_name': 'Georgia'})
        wbf['content_number'].set_right()
        wbf['content_number'].set_left()

        wbf['content_percent'] = workbook.add_format(
            {'align': 'right', 'num_format': '0.00%', 'font_name': 'Georgia'})
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
            {'align': 'right', 'bg_color': colors['yellow'], 'bold': 1, 'num_format': '#,##0',
             'font_name': 'Georgia'})
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
            {'align': 'right', 'bg_color': colors['orange'], 'bold': 1, 'num_format': '#,##0',
             'font_name': 'Georgia'})
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

    def get_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'date_start': self.date_start, 'date_end': self.date_end, 'company_id': self.company_id.id,
                'branch_id': self.branch_ids.id,
                'branch_name': self.branch_ids.name, 'payment_method': self.payment_method.id,
            },
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('accounting_report.account_collection_statement_report').report_action(
            self, data=data)


class CollectionStatementReportView(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.accounting_report.collection_statement_report_view'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        branch_id = data['form']['branch_id']
        branch_name = data['form']['branch_name']
        payment_method = data['form']['payment_method']
        company_id = data['form']['company_id']

        if payment_method:
            payment_method = " ap.payment_method_id  = %s" % payment_method
        else:
            payment_method = "1=1"

        if branch_id:
            branch_id = " ap.branch_id = %s" % branch_id

        else:
            branch_id = "1=1"

        if company_id:
            company_id = " am.company_id = %s" % company_id

        else:
            company_id = "1=1"

        query = """
                           select distinct to_char(ap.create_date,'DD-MON-YYYY') create_date, aj.name as payment_type, pm.name as paymentMethod, res_p.name as buyer, e.name as sales_person, ap.name as money_recipt, eap.name as collected_by, ap.communication as invoice_no, ap.amount as collected_amount,ap.branch_id,br.name as branch_name 
                           from account_payment ap 
                           left join account_move am  on ap.move_name = am.name and am.state='posted'
                           left join hr_employee eap on ap.create_uid = eap.user_id
                           left join res_partner res_p on am.partner_id = res_p.id
                           left join account_journal aj on ap.journal_id = aj.id
                           left join account_payment_method pm on ap.payment_method_id = pm.id
                           left join account_move amc on ap.communication = amc.invoice_payment_ref and amc.state='posted'
                           left join hr_employee e on amc.create_uid = e.user_id
                           left join res_branch br on br.id=ap.branch_id
                           where ap.payment_type = 'inbound' and ap.state='posted' and ap.partner_type <> 'supplier' and {} and ap.payment_date::date between '{}' and '{}' and {} and {} and am.company_id=br.company_id
                            ORDER BY create_date, br.name, aj.name, pm.name, res_p.name , e.name, ap.name, eap.name, ap.communication, ap.amount,ap.branch_id
                           """.format(branch_id, date_start, date_end, payment_method, company_id)
        # For Batch Payment
        # query = """
        #     select distinct ap.payment_date::DATE payment_date, aj.name as payment_type, pm.name as paymentMethod, res_p.name as buyer, sp.name as sales_person, bp.name as money_recipt, collector.name as collected_by, ap.communication as invoice_no, ap.amount as collected_amount,ap.branch_id,br.name as branch_name
        #     from account_payment ap
        #     left join account_move am  on ap.move_name = am.name and am.state='posted'
        #     left join batch_payment bp on bp.id = ap.batch_payment_id
        #     left join res_partner collector on collector.id = bp.collected_by
        #     left join res_partner res_p on am.partner_id = res_p.id
        #     left join account_journal aj on ap.journal_id = aj.id
        #     left join account_payment_method pm on ap.payment_method_id = pm.id
        #     left join res_partner sp on sp.id = res_p.user_id
        #     left join res_branch br on br.id=ap.branch_id
        #     where ap.payment_type = 'inbound' and ap.state='posted' and ap.partner_type <> 'supplier' and {} and ap.payment_date::date between '{}' and '{}' and {} and {} and am.company_id=br.company_id
        #      ORDER BY payment_date, br.name, aj.name, pm.name, res_p.name, ap.communication, ap.amount,ap.branch_id
        #     """.format(branch_id, date_start, date_end, payment_method, company_id)

        self._cr.execute(query=query)
        query_result = self._cr.fetchall()
        # print("query_result_pdf:",query_result)
        # collection_statements = dict()
        # for collection in query_result:
        #     collection_date = str(collection[0].date())
        #     if collection_date not in collection_statements.keys():
        #         collection_statements[collection_date] = dict()
        #     if collection[2] not in collection_statements[collection_date].keys():
        #         collection_statements[collection_date][collection[2]] = dict()
        #     if collection[1] in collection_statements[collection_date][collection[2]].keys():
        #         collection_statements[collection_date][collection[2]][collection[1]].append(collection)
        #     else:
        #         collection_statements[collection_date][collection[2]][collection[1]] = list()
        #         collection_statements[collection_date][collection[2]][collection[1]].append(collection)

        collection_statements = dict()
        for collection in query_result:
            print(collection[10])
            print(collection[0])
            collection_date = collection[0]
            if collection_date not in collection_statements.keys():
                collection_statements[collection_date] = dict()
            if collection[10] not in collection_statements[collection_date].keys():
                collection_statements[collection_date][collection[10]] = dict()
            if collection[2] not in collection_statements[collection_date][collection[10]].keys():
                collection_statements[collection_date][collection[10]][collection[2]] = dict()
            if collection[1] in collection_statements[collection_date][collection[10]][collection[2]].keys():
                collection_statements[collection_date][collection[10]][collection[2]][collection[1]].append(collection)
            else:
                collection_statements[collection_date][collection[10]][collection[2]][collection[1]] = list()
                collection_statements[collection_date][collection[10]][collection[2]][collection[1]].append(collection)

            print("collection_statements_pdf:", collection_statements)

        total_collection = dict()
        date_wise_payment_method = dict()
        branch_wise_payment_method = dict()

        for single_collection in query_result:
            # print(single_collection)
            # # Date wise payment
            collection_date = single_collection[0]
            # if collection_date not in date_wise_payment_method.keys():
            #     date_wise_payment_method[collection_date] = dict()
            #
            # # if single_collection[2] not in date_wise_payment_method[collection_date].keys():
            # #     date_wise_payment_method[collection_date][single_collection[2]] = single_collection[-3]
            #
            # if single_collection[10] not in date_wise_payment_method[collection_date].keys():
            #     date_wise_payment_method[collection_date][single_collection[10]] = dict()
            #
            # if single_collection[2] not in date_wise_payment_method[collection_date][single_collection[10]].keys():
            #     date_wise_payment_method[collection_date][single_collection[10]][single_collection[2]] = single_collection[-3]
            # else:
            #     date_wise_payment_method[collection_date][single_collection[10]][single_collection[2]] += single_collection[-3]

            # branch wise payment
            if single_collection[10] not in branch_wise_payment_method.keys():
                branch_wise_payment_method[single_collection[10]] = dict()

            if collection_date not in branch_wise_payment_method[single_collection[10]].keys():
                branch_wise_payment_method[single_collection[10]][collection_date] = dict()

            if single_collection[2] not in branch_wise_payment_method[single_collection[10]][collection_date].keys():
                branch_wise_payment_method[single_collection[10]][collection_date][single_collection[2]] = \
                    single_collection[-3]
            else:
                branch_wise_payment_method[single_collection[10]][collection_date][single_collection[2]] += \
                    single_collection[-3]

            # # Date wise payment
            # br_name = str(single_collection[10])
            if collection_date not in date_wise_payment_method.keys():
                date_wise_payment_method[collection_date] = dict()
            if single_collection[2] not in date_wise_payment_method[collection_date].keys():
                date_wise_payment_method[collection_date][single_collection[2]] = single_collection[-3]
            else:
                date_wise_payment_method[collection_date][single_collection[2]] += single_collection[-3]

            # total payment
            if single_collection[2] not in total_collection.keys():
                total_collection[single_collection[2]] = single_collection[-3]
            else:
                total_collection[single_collection[2]] += single_collection[-3]

        print("date_wise_payment_method_pdf", date_wise_payment_method)
        print("total_collection_pdf:", total_collection)
        print("branch_wise_payment_method_pdf:", branch_wise_payment_method)

        # print(date_wise_payment_method)
        # print(total_collection)
        # for key, value in total_collection.items():
        #     print(key, value)

        # for date, date_value in collection_statements.items():
        #     print(date)
        #     for p_type, p_type_value in date_value.items():
        #         total_collection[p_type] = 0
        #         print(p_type)
        #         for journal, journal_value in p_type_value.items():
        #             print(journal)
        #             for c in journal_value:
        #                 print(c)

        return {
            'date_start': date_start,
            'date_end': date_end,
            'branch': branch_name,
            'collection_statements': collection_statements,
            'date_wise_payment_method': date_wise_payment_method,
            'total_collection': total_collection,
            'username': self.env.user.name,
            'branch_wise_payment_method': branch_wise_payment_method,
        }
