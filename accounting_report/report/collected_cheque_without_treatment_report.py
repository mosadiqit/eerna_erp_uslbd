from odoo import models


class CheckWithoutTreatment(models.AbstractModel):
    _name = 'report.accounting_report.cheque_without_treatment_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        dict_data = []
        customer_group = []
        for single_data in data['result']:
            val = {
                'customer': single_data[0] if single_data[0] else '',
                'Cheque_No': single_data[1] if single_data[1] else '',
                'rec_date': single_data[2] if single_data[2] else '',
                'cheque_date': single_data[3] if single_data[3] else '',
                'bank_name': single_data[4] if single_data[4] else '',
                'collection_no': single_data[5] if single_data[5] else '',
                'salesperson': single_data[6] if single_data[6] else '',
                'amount': int(single_data[7]) if single_data[7] else 0,

            }
            dict_data.append(val)
            if single_data[0] not in customer_group:
                customer_group.append(single_data[0])

        # format1 = workbook.add_format({'font_size': 14, 'align': 'center', 'bold': True})
        # format2 = workbook.add_format({'font_size': 10, 'align': 'center'})
        merge_format = workbook.add_format({
            'font_size': 16,
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#D7DBDD'
        })
        merge_format2 = workbook.add_format({
            'font_size': 12.5,

            'border': 1,
            'fg_color': '#F2F3F4'
        })
        heading_format = workbook.add_format({
            'fg_color': '#ABEBC6',
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 14,

        })
        bold_format = workbook.add_format({
            'bold': 1,
        })
        sheet = workbook.add_worksheet("collected cheque without treatment")
        sheet.write(5, 0, 'Cheque No', heading_format)
        sheet.write(5, 1, 'Rec Date', heading_format)
        sheet.write(5, 2, 'Cheque Date', heading_format)
        sheet.write(5, 3, 'Bank Name', heading_format)
        sheet.write(5, 4, 'Collection No', heading_format)
        sheet.write(5, 5, 'S.Person', heading_format)
        sheet.write(5, 6, 'Amount', heading_format)

        sheet.set_column('A:U', 20)
        # sheet.set_row(3, 30)
        sheet.set_row(5, 30)
        # sheet.set_row(7, 30)
        sheet.freeze_panes(6, 0)

        sheet.merge_range('C2:E4',
                          f"Collected Cheque Without Treatment Report\n {data['date_start']}  to  {data['date_end']}",
                          merge_format)
        i = 8
        a = True
        grand_total = 0
        for customer in customer_group:
            if a:
                sheet.merge_range(f'A{i}:G{i}', 'Buyer Group', merge_format2)
                a = False

            sheet.merge_range(f'A{i + 1}:G{i + 1}', f'Customer Name : {customer}', merge_format2)
            i += 1
            amount_sum = []
            subtotal = 0
            for data_val in dict_data:

                if customer == data_val['customer']:
                    sheet.write(i, 0, data_val['Cheque_No'])
                    sheet.write(i, 1, data_val['rec_date'])
                    sheet.write(i, 2, data_val['cheque_date'])
                    sheet.write(i, 3, data_val['bank_name'])
                    sheet.write(i, 4, data_val['collection_no'])
                    sheet.write(i, 5, data_val['salesperson'])
                    sheet.write(i, 6, data_val['amount'])
                    i += 1
                    subtotal += data_val['amount']
                    # amount_sum.append(int(data_val['amount']))
            grand_total += subtotal
            # print(sum(amount_sum))
            sheet.write(i, 5, 'subtotal', bold_format)
            sheet.write(i, 6, subtotal, bold_format)
            i += 1
        if grand_total:
            i += 1
            sheet.write(i, 5, 'Grand Total', bold_format)
            sheet.write(i, 6, grand_total, bold_format)
