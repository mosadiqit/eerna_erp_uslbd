from odoo import models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, datetime, relativedelta


class SaleGrossProfitView(models.AbstractModel):
    _name = 'report.accounting_report.sale_gross_profit_view_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        branch_id = data['form']['branch_id']
        company_id = data['form']['company_id']
        product_ids = data['form']['product_ids']
        categ_ids = data['form']['categ_ids']
        group_ids = data['form']['group_ids']
        brand_ids = data['form']['brand_ids']
        model_ids = data['form']['model_ids']
        partner_ids = data['form']['partner_ids']
        partner_tags = data['form']['partner_tags']


        new_branch_id = []
        x = branch_id.split("(")
        y = x[1].split(")")
        z = y[0].split(",")
        if z[0] != '':

            new_branch_id = [int(x) for x in z if x != '']
        else:
            where_branch_id = "1=1"

        if company_id:
            company_id = " c_id = %s" % company_id

        else:
            company_id = "1=1"
        # branch_name = data['form']['branch_name']

        start_date = datetime.strptime(date_start, DATE_FORMAT)
        end_date = datetime.strptime(date_end, DATE_FORMAT)
        date = (end_date + relativedelta(days=+ 1))



        view_refresh = """REFRESH MATERIALIZED VIEW mvw_sales_gross_profit"""
        self._cr.execute(query=view_refresh)

        final_query = """select br_name,invoice_date,invoice_id,invoice_no,COALESCE(sum(bill_amount),0),COALESCE(sum(cost_amount),0)
                                ,COALESCE(sum(bill_amount),0)-COALESCE(sum(cost_amount),0) as sales_profit from mvw_sales_gross_profit 
                                 where {} and {} and invoice_date between '{}' and '{}' group
                                 by 1,2,3,4 order by 2""".format(company_id, where_branch_id,
                                                                 start_date.strftime(DATETIME_FORMAT),
                                                                 end_date.strftime(DATETIME_FORMAT))

        self._cr.execute(query=final_query)
        query_result = self._cr.fetchall()
        profit_statement = dict()
        for res in query_result:
            if res[0] in profit_statement.keys():
                profit_statement[res[0]].append(res)
            else:
                profit_statement[res[0]] = list()
                profit_statement[res[0]].append(res)

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
            'fg_color': 'yellow'
        })
        heading_format = workbook.add_format({
            'fg_color': '#ABEBC6',
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 14,

        })
        center_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
        })
        bold_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'bold': 1,
            'font_size': 11,
            'fg_color': '#D7DBDD'

        })
        sheet = workbook.add_worksheet("Sales Gross Profit")


        # sheet.set_row(5, 30)
        sheet.set_column('A:F', 22)
        sheet.merge_range('C2:E4',
                          f"Stock Gross Profit Statement\n From:{data['form']['date_start']}  To:{data['form']['date_end']}",
                          merge_format)
        sheet.write(6, 0, 'SL', heading_format)
        sheet.write(6, 1, 'Date', heading_format)
        sheet.write(6, 2, 'Invoice', heading_format)
        sheet.write(6, 3, 'Bill Amount', heading_format)
        sheet.write(6, 4, 'Cost Amount', heading_format)
        sheet.write(6, 5, 'Margin Amount', heading_format)
        sheet.set_row(6, 30)
        sheet.freeze_panes(7, 0)
        i = 8
        grand_total = bill_grand = cost_grand = 0
        for branch in profit_statement.keys():
            subtotal = bill_amount = cost_amount = 0
            sheet.merge_range(f'A{i}:F{i}', branch, merge_format2)
            i += 1
            for id, value in enumerate(profit_statement[branch], start=1):
                sheet.write(i, 0, id, center_format)
                sheet.write(i, 1, str(value[1]), center_format)
                sheet.write(i, 2, value[3], center_format)
                sheet.write(i, 3, float(value[4]), center_format)
                sheet.write(i, 4, float(value[5]), center_format)
                sheet.write(i, 5, float(value[6]), center_format)
                i += 1
                subtotal += value[6]
                cost_amount += value[5]
                bill_amount += value[4]

            sheet.write(i, 0, '', bold_format)
            sheet.write(i, 1, '', bold_format)
            sheet.write(i, 2, f'{branch} Total', bold_format)
            sheet.write(i, 3, bill_amount, bold_format)
            sheet.write(i, 4, cost_amount, bold_format)
            sheet.write(i, 5, subtotal, bold_format)
            i += 2
            grand_total += subtotal
            cost_grand += cost_amount
            bill_grand += bill_amount
        if grand_total or bill_grand or cost_grand:
            sheet.write(i, 0, '', bold_format)
            sheet.write(i, 1, '', bold_format)
            sheet.write(i, 2, 'Grand Total', bold_format)
            sheet.write(i, 3, bill_grand, bold_format)
            sheet.write(i, 4, cost_grand, bold_format)
            sheet.write(i, 5, grand_total, bold_format)

