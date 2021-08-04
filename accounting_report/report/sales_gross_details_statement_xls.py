from odoo import models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, datetime, relativedelta


class CollectionStatementReportViewXml(models.AbstractModel):
    _name = 'report.accounting_report.sale_gross_profit_details_view_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        print(self)
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        branch_id = data['form']['branch_id']
        company_id = data['form']['company_id']
        neg = data['form']['negetive']

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

        if new_branch_id:
            if len(new_branch_id) == 1:
                where_branch_id = " br_id =%s" % new_branch_id[0]
            else:
                # where_branch_id ="br_id=%s"%branch_id
                where_branch_id = " br_id in %s" % str(tuple(new_branch_id))

        view_refresh = """REFRESH MATERIALIZED VIEW mvw_sales_gross_profit_details"""
        self._cr.execute(query=view_refresh)

        final_query = """select br_name,invoice_date,invoice_id,invoice_no,product_name,quantity,COALESCE(sum(bill_amount),0),COALESCE(sum(cost_amount),0)
                        ,COALESCE(sum(bill_amount),0)-COALESCE(sum(cost_amount),0) as sales_profit,(COALESCE(sum(bill_amount),0)-COALESCE(sum(cost_amount),0))*100/case when COALESCE(sum(cost_amount),0)=0 then 1 else COALESCE(sum(cost_amount),0) end as profit_margin from mvw_sales_gross_profit_details 
                         where {} and {} and invoice_date between '{}' and '{}' group
                         by 1,2,3,4,5,6 order by 2""".format(company_id, where_branch_id,
                                                             start_date.strftime(DATETIME_FORMAT),
                                                             end_date.strftime(DATETIME_FORMAT))
        neq_query = """select * from (select br_name,invoice_date,invoice_id,invoice_no,product_name,quantity,COALESCE(sum(bill_amount),0),COALESCE(sum(cost_amount),0)
                        ,COALESCE(sum(bill_amount),0)-COALESCE(sum(cost_amount),0) as sales_profit,(COALESCE(sum(bill_amount),0)-COALESCE(sum(cost_amount),0))*100/case when COALESCE(sum(cost_amount),0)=0 then 1 else COALESCE(sum(cost_amount),0) end as profit_margin from mvw_sales_gross_profit_details 
                         where {} and {}  and invoice_date between '{}' and '{}' group
                         by 1,2,3,4,5,6 order by 2) as nnm where profit_margin <0""".format(company_id, where_branch_id,
                                                                                            start_date.strftime(
                                                                                                DATETIME_FORMAT),
                                                                                            end_date.strftime(
                                                                                                DATETIME_FORMAT))
        if neg:
            self._cr.execute(query=neq_query)
        else:
            self._cr.execute(query=final_query)
        query_result = self._cr.fetchall()
        profit_statement = dict()
        for res in query_result:
            if res[0] not in profit_statement.keys():
                profit_statement[res[0]] = dict()
            if res[3] in profit_statement[res[0]].keys():
                profit_statement[res[0]][res[3]].append(res)
            else:
                profit_statement[res[0]][res[3]] = list()
                profit_statement[res[0]][res[3]].append(res)

        # excel report formatting

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
            'fg_color': '#DEDAA7'

        })
        merge_format3 = workbook.add_format({
            'font_size': 12.5,
            'border': 1,
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
        center_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
        })
        bold_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'bold': 1,
            'font_size': 11,
            'fg_color': '#F5F5EE'

        })
        bold_format2 = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'bold': 1,
            'font_size': 11,
            'fg_color': '#EBEAD8'

        })
        bold_format3 = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'bold': 1,
            'font_size': 11,
            'fg_color': '#E1D644'

        })
        font_9 = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 9,
        })

        sheet = workbook.add_worksheet("Sales Gross Profit Details Statement")
        sheet.set_column('D:H', 15)
        sheet.set_column('B:B', 10)
        sheet.set_column('C:C', 60)
        sheet.set_default_row(25)
        sheet.merge_range('C1:E2',
                          f"Sales Gross Profit Details Statement\n From:{data['form']['date_start']}  To:{data['form']['date_end']}",
                          merge_format)
        sheet.write(3, 0, 'SL', heading_format)
        sheet.write(3, 1, 'Date', heading_format)
        sheet.write(3, 2, 'Product Name', heading_format)
        sheet.write(3, 3, 'Quantity', heading_format)
        sheet.write(3, 4, 'Bill Amount', heading_format)
        sheet.write(3, 5, 'Cost Amount', heading_format)
        sheet.write(3, 6, 'Margin Amount', heading_format)
        sheet.write(3, 7, 'Margin %', heading_format)
        sheet.freeze_panes(4, 0)

        i = 5
        grand_bill = grand_cost = grand_margin = 0
        for branch in profit_statement.keys():
            branch_bill = branch_cost = branch_margin = 0
            sheet.merge_range(f'A{i}:H{i}', branch, merge_format2)
            i += 1
            for invoice in profit_statement[branch].keys():
                invoice_bill = invoice_cost = invoice_margin = 0
                sheet.merge_range(f'A{i}:H{i}', invoice, merge_format3)
                # i += 1
                for id, value in enumerate(profit_statement[branch][invoice], start=1):
                    sheet.write(i, 0, id, center_format)
                    sheet.write(i, 1, str(value[1]), center_format)
                    sheet.write(i, 2, value[4], font_9)
                    sheet.write(i, 3, value[5], center_format)
                    sheet.write(i, 4, value[6], center_format)
                    sheet.write(i, 5, value[7], center_format)
                    sheet.write(i, 6, value[8], center_format)
                    sheet.write(i, 7, '%.2f' % value[9], center_format)
                    i += 1
                    invoice_bill += value[6]
                    invoice_cost += value[7]
                    invoice_margin += value[8]
                # i += 1
                sheet.write(i, 0, '', bold_format)
                sheet.write(i, 1, '', bold_format)
                sheet.write(i, 2, f"{invoice} Total", bold_format)
                sheet.write(i, 3, '', bold_format)
                sheet.write(i, 4, invoice_bill, bold_format)
                sheet.write(i, 5, invoice_cost, bold_format)
                sheet.write(i, 6, invoice_margin, bold_format)
                sheet.write(i, 7, '', bold_format)
                i += 2
                branch_bill += invoice_bill
                branch_cost += invoice_cost
                branch_margin += invoice_margin
            sheet.write(i, 0, '', bold_format2)
            sheet.write(i, 1, '', bold_format2)
            sheet.write(i, 2, f"{branch} Total", bold_format2)
            sheet.write(i, 3, '', bold_format2)
            sheet.write(i, 4, branch_bill, bold_format2)
            sheet.write(i, 5, branch_cost, bold_format2)
            sheet.write(i, 6, branch_margin, bold_format2)
            sheet.write(i, 7, '', bold_format2)
            i += 2
            grand_bill += branch_bill
            grand_cost += branch_cost
            grand_margin += branch_margin
        sheet.write(i, 0, '', bold_format3)
        sheet.write(i, 1, '', bold_format3)
        sheet.write(i, 2, "Grand Total", bold_format3)
        sheet.write(i, 3, '', bold_format3)
        sheet.write(i, 4, grand_bill, bold_format3)
        sheet.write(i, 5, grand_cost, bold_format3)
        sheet.write(i, 6, grand_margin, bold_format3)
        sheet.write(i, 7, '', bold_format3)
        i += 1

