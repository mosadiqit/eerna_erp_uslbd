from odoo import models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, datetime, relativedelta


class CollectionStatementReportViewXml(models.AbstractModel):
    _name = 'report.accounting_report.payment_statement_report_view_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
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
                    select to_char(ap.create_date,'DD-MON-YYYY') create_date, aj.name as payment_type, pm.name as paymentMethod, res_p.name as buyer, e.name as sales_person, ap.move_name as money_recipt, e.name as collected_by, ap.communication as invoice_no, ap.amount as collected_amount,ap.branch_id,br.name as branch_name  
                    from account_payment ap 
                    left join account_move am  on ap.move_name = am.name
                    left join hr_employee eap on ap.create_uid = eap.user_id
                    left join res_partner res_p on am.partner_id = res_p.id
                    left join account_journal aj on ap.journal_id = aj.id
                    left join account_payment_method pm on ap.payment_method_id = pm.id
                    left join account_move amc on ap.communication = amc.invoice_payment_ref
                    left join hr_employee e on amc.create_uid = e.user_id
                    left join res_branch br on br.id=ap.branch_id
                    where ap.payment_type = 'outbound'  and ap.partner_type <> 'customer' and ap.state='posted' and {} and {}  and ap.create_date::date between '{}' and '{}' and {}
                    ORDER BY ap.create_date,br.name
                    """.format(branch_id, company_id, date_start, date_end, payment_method)

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
        print('collection_statements', collection_statements)

        merge_format = workbook.add_format({
            'font_size': 16,
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#D7DBDD'
        })

        heading_format = workbook.add_format({
            'fg_color': '#ABEBC6',
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 12,

        })
        merge_format2 = workbook.add_format({
            'font_size': 13.5,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'fg_color': '#D7DBDD'
        })
        merge_format3 = workbook.add_format({
            'font_size': 12,
            'border': 1,
            'fg_color': '#D7DBDD'
        })
        center_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
        })
        sheet = workbook.add_worksheet("Payment Statement")
        sheet.set_column('B:H', 20)
        sheet.set_row(4, 30)
        # sheet.set_column('B:B', 10)
        # sheet.set_column('C:C', 60)
        # sheet.set_default_row(40)
        sheet.merge_range('C1:F3',
                          f"Payment Statement\n From:{data['form']['date_start']}  To:{data['form']['date_end']}",
                          merge_format)
        sheet.write(4, 0, 'SL', heading_format)
        sheet.write(4, 1, 'Party', heading_format)
        sheet.write(4, 2, 'Contact Person', heading_format)
        sheet.write(4, 3, 'Receipt No', heading_format)
        sheet.write(4, 4, 'Payment By', heading_format)
        sheet.write(4, 5, 'Invoice No', heading_format)
        sheet.write(4, 6, 'Payment Amount', heading_format)
        sheet.freeze_panes(4, 0)
        row = 6
        grand_total = 0
        grnad_check_total = 0
        grand_cash_total = 0
        for date in collection_statements.keys():
            date_total = 0
            date_check_total = 0
            date_cash_total = 0
            sheet.merge_range(f'A{row}:G{row}', f'{date}', merge_format2)
            row += 1
            for branch_name in collection_statements[date].keys():
                branch_total = 0
                branch_check_total = 0
                branch_cash_total = 0
                sheet.merge_range(f'A{row}:G{row}', f'{branch_name}', merge_format2)
                row += 1
                for payment in collection_statements[date][branch_name].keys():
                    payment_total = 0
                    payment_check_total = 0
                    payment_cash_total = 0
                    sheet.merge_range(f'A{row}:G{row}', f'{payment}', merge_format2)
                    row += 1
                    for payment_details in collection_statements[date][branch_name][payment].keys():
                        payment_details_total = 0

                        sheet.merge_range(f'A{row}:G{row}', f'{payment_details}', merge_format2)
                        row += 1
                        for index, single_data in enumerate(
                                collection_statements[date][branch_name][payment][payment_details], start=1):
                            sheet.write(row, 0, index, center_format)
                            sheet.write(row, 1, single_data[3], center_format)
                            sheet.write(row, 2, single_data[4], center_format)
                            sheet.write(row, 3, single_data[5], center_format)
                            sheet.write(row, 4, single_data[6], center_format)
                            sheet.write(row, 5, f'{"Partial Payment" if single_data[7] is None else single_data[7]}',
                                        center_format)
                            sheet.write(row, 6, single_data[8], center_format)
                            row += 1
                            payment_details_total += single_data[8]
                            payment_total += single_data[8]
                            branch_total += single_data[8]
                            date_total += single_data[8]
                            grand_total += single_data[8]
                            if single_data[2] == 'Checks':
                                payment_check_total += single_data[8]
                                branch_check_total += single_data[8]
                                date_check_total += single_data[8]
                                grnad_check_total += single_data[8]
                            else:
                                payment_cash_total += single_data[8]
                                branch_cash_total += single_data[8]
                                date_cash_total += single_data[8]
                                grand_cash_total += single_data[8]
                        sheet.write(row, 1, f'total {payment_details} Amount', center_format)
                        sheet.write(row, 6, payment_details_total, center_format)
                        row += 1
                    sheet.write(row, 1, f'total {payment} Amount', center_format)
                    if payment == 'Checks':
                        sheet.write(row, 6, payment_check_total, center_format)
                    else:
                        sheet.write(row, 6, payment_cash_total, center_format)

                    row += 2
                sheet.merge_range(f'A{row}:G{row}', f'Total of {branch_name}', merge_format2)
                row += 1
                sheet.write(row, 1, f'total Cash Amount', center_format)
                sheet.write(row, 6, branch_cash_total, center_format)
                row += 1
                sheet.write(row, 1, f'total Check Amount', center_format)
                sheet.write(row, 6, branch_check_total, center_format)
                row += 1
                sheet.write(row, 1, f'total  Amount', center_format)
                sheet.write(row, 6, branch_total, center_format)
                row += 2
            sheet.merge_range(f'A{row}:G{row}', f'Total of {date}', merge_format2)
            row += 1
            sheet.write(row, 1, f'total Cash Amount', center_format)
            sheet.write(row, 6, date_cash_total, center_format)
            row += 1
            sheet.write(row, 1, f'total Check Amount', center_format)
            sheet.write(row, 6, date_check_total, center_format)
            row += 1
            sheet.write(row, 1, f'total  Amount', center_format)
            sheet.write(row, 6, date_total, center_format)
            row += 2
        sheet.merge_range(f'A{row}:G{row}', f'Grand Total', merge_format2)
        row += 1
        sheet.write(row, 1, f'total Cash Amount', center_format)
        sheet.write(row, 6, grand_cash_total, center_format)
        row += 1
        sheet.write(row, 1, f'total Check Amount', center_format)
        sheet.write(row, 6, grnad_check_total, center_format)
        row += 1
        sheet.write(row, 1, f'total  Amount', center_format)
        sheet.write(row, 6, grand_total, center_format)
        row += 1

        # for date_wise in collection_statements.keys():
        #     date_wise_total = 0
        #     sheet.merge_range(f'A{i}:G{i}', f'{date_wise}', merge_format2)
        #     i += 1
        #
        #     for branch_wise in collection_statements[date_wise].keys():
        #         branch_wise_total = 0
        #         sheet.merge_range(f'A{i}:G{i}', f'{branch_wise}', merge_format2)
        #         i += 1
        #
        #         for payment in collection_statements[date_wise][branch_wise].keys():
        #             payment_wise_total = 0
        #             sheet.merge_range(f'A{i}:G{i}', f'{payment}', merge_format3)
        #             i += 1
        #
        #             for party in collection_statements[date_wise][branch_wise][payment].keys():
        #                 checks_total = None
        #                 cash_total = None
        #                 party_total = 0
        #                 sheet.merge_range(f'A{i}:G{i}', f'{party}', merge_format3)
        #                 for id, single_data in enumerate(collection_statements[date_wise][branch_wise][payment][party],
        #                                                  start=1):
        #                     sheet.write(i, 0, id, center_format)
        #                     sheet.write(i, 1, single_data[3], center_format)
        #                     sheet.write(i, 2, single_data[4], center_format)
        #                     sheet.write(i, 3, single_data[5], center_format)
        #                     sheet.write(i, 4, single_data[6], center_format)
        #                     sheet.write(i, 5, f'{"Partial Payment" if single_data[7] is None else single_data[7]}',
        #                                 center_format)
        #                     sheet.write(i, 6, single_data[8], center_format)
        #                     party_total += single_data[8]
        #                     i += 1
        #                 sheet.write(i, 1, f'total {party} Amount', center_format)
        #                 sheet.write(i, 6, party_total, center_format)
        #                 i += 2
        #                 payment_wise_total += party_total
        #             print(date_wise)
        #             if payment == 'Cash':
        #                 cash_total = payment_wise_total
        #                 print('cash_total', cash_total)
        #             if payment == 'Checks':
        #                 checks_total = payment_wise_total
        #                 print('Checks_total', checks_total)
        #
        #             sheet.write(i, 1, f'total {payment} Amount', center_format)
        #             sheet.write(i, 6, payment_wise_total, center_format)
        #             i += 1
        #             branch_wise_total += payment_wise_total
        #         sheet.merge_range(f'A{i + 1}:G{i + 1}', f'Total of {branch_wise}', merge_format2)
        #         i += 1
        #         sheet.write(i, 1, f'total {branch_wise} Amount', center_format)
        #         sheet.write(i, 6, branch_wise_total, center_format)
        #         i += 1
        #         date_wise_total += branch_wise_total
        #     sheet.merge_range(f'A{i + 1}:G{i + 1}', f'Total of {date_wise}', merge_format2)
        #     i += 2
        #     if checks_total:
        #         sheet.write(i, 1, 'Check total', center_format)
        #         sheet.write(i, 6, checks_total, center_format)
        #         i += 1
        #     if cash_total:
        #         sheet.write(i, 1, 'Cash total', center_format)
        #         sheet.write(i, 6, cash_total, center_format)
        #         i += 1
        #     sheet.write(i, 1, f'total Amount', center_format)
        #     sheet.write(i, 6, date_wise_total, center_format)
        #     i += 2
