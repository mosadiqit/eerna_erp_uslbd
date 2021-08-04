import json
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, BytesIO, xlsxwriter, base64
import pytz
from pytz import timezone


class StockTransferReportWizard(models.TransientModel):
    _name = 'stock.transfer.report.wizard'

    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone(self.env.user.tz or 'UTC'))

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Date', required=True, default=fields.Date.today)
    company_id = fields.Many2one('res.company', string='Company', domain=lambda self: self._get_companies(),
                                 default=lambda self: self.env.user.company_id, required=True)
    from_branch_id = fields.Many2one('stock.location', string='From Branch')
    to_branch_id = fields.Many2one('stock.location', string='To Branch')

    @api.onchange('from_branch_id','to_branch_id')
    def check_users_branch(self):
        location_id = self.env['stock.location'].search([('branch_id', '=', self.env.user.branch_ids.ids)])
        all_location = self.env['stock.location'].search([('usage','=','internal')])
        if self.user_has_groups('stock.group_stock_manager'):
            m_location_id = self.env['stock.location'].search(
                [('usage', '=', 'internal'), ('branch_id', '=', self.env.user.branch_ids.ids)])
            # return [('id','in',m_location_id.ids)]
            return {'domain': {'from_branch_id': [('id', 'in', m_location_id.ids)],'to_branch_id': [('id', 'in', all_location.ids)]}}
            # self.location_ids = m_location_id
        elif self.user_has_groups('stock.group_stock_user'):
            return {'domain': {'from_branch_id': [('id', 'in', location_id.ids)],'to_branch_id': [('id', 'in', all_location.ids)]}}


    def _get_companies(self):
        print(self.env.user)
        query = """select * from res_company_users_rel where user_id={}""".format(self.env.user.id)
        self._cr.execute(query=query)
        allowed_companies = self._cr.fetchall()
        print(allowed_companies)
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
                'from_branch_id': self.from_branch_id.id, 'to_branch_id': self.to_branch_id.id
            },
        }

        start_date = data['form']['date_start']
        end_date = data['form']['date_end']
        company_id = data['form']['company_id']
        from_branch_id = data['form']['from_branch_id']
        to_branch_id = data['form']['to_branch_id']
        # branch_name = data['form']['branch_name']

        # start_date = datetime.strptime(start_date, DATE_FORMAT)
        # end_date = datetime.strptime(date_end, DATE_FORMAT)
        date = (end_date + relativedelta(days=+ 1))
        # e_date=end_date.date()+datetime.timedelta(days=1)

        # print(start_date + "------" + date.strftime(DATETIME_FORMAT))

        if from_branch_id:
            where_from_branch_id = 'sp.location_id=%s' % from_branch_id
        else:
            where_from_branch_id = '1=1'
        if to_branch_id:
            where_to_branch_id = 'sp.location_dest_id=%s' % to_branch_id
        else:
            where_to_branch_id = '1=1'

        docs = []

        query = """
                    select sp.name as reference_name,sl.complete_name as from_branch,sl1.complete_name as to_branch, sp.create_date,sp.id,sp.state from stock_picking sp 
                    left join stock_location sl on sl.id=sp.location_id
                    left join stock_location sl1 on sl1.id=sp.location_dest_id
                    left join stock_picking_type spt on spt.id=sp.picking_type_id
                    where {} and {} and  sp.date between '{}' and '{}' and sp.state = '{}' and spt.sequence_code='{}' and sp.company_id={} order by sp.create_date asc
                    """.format(where_from_branch_id, where_to_branch_id, start_date.strftime(DATETIME_FORMAT),
                               date.strftime(DATETIME_FORMAT), "done", "INT", company_id)

        self._cr.execute(query=query)
        query_result = self._cr.fetchall()

        collection_statements = dict()

        for collection in query_result:
            create_date = collection[3].date()
            if create_date in collection_statements.keys():
                collection_statements[create_date].append(collection)
            else:
                collection_statements[create_date] = list()
                collection_statements[create_date].append(collection)
        print(collection_statements)
        all_product_based_move_id = []

        filtered_by_date_branch = list()
        total_orders = len(filtered_by_date_branch)
        # amount_total = sum(order.amount_total for order in filtered_by_date_branch)
        allsale = []
        allsale = filtered_by_date_branch

        docs.append({
            'date': start_date.strftime("%Y-%m-%d"),
            'total_orders': total_orders,
            # 'amount_total': amount_total,
            'company': self.env.user.company_id,

        })
        # New
        report_name = 'Stock Transfer Report'
        filename = '%s' % (report_name)
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf, workbook = self.add_workbook_format(workbook)
        worksheet = workbook.add_worksheet(report_name)
        worksheet.merge_range('A2:D3', report_name, wbf['title_doc'])
        columns = [
            ('Date and Reference', 30, 'no', 'no'),
            ('From', 50, 'char', 'char'),
            ('To', 20, 'char', 'char'),
            ('Status', 20, 'char', 'char'),
        ]

        row = 4

        col = 0
        # row = 6
        grand_total = 0
        for column in columns:
            column_name = column[0]
            column_width = column[1]
            column_type = column[2]
            worksheet.set_column(col, col, column_width)
            worksheet.write(row - 1, col, column_name, wbf['header_orange'])
            # worksheet.merge_range('A2:I3', column_name, wbf['header_orange'])
            col += 1
        row += 2

        col1 = 0

        cloumn_product = [
            ('SL', 20, 'char', 'no'),
            ('Product', 60, 'char', 'no'),
            ('Qty', 40, 'float', 'float'),

        ]
        for coll in collection_statements.keys():

            worksheet.merge_range('A%s:D%s' % (row, row), str(coll), wbf['header_orange'])
            row += 1
            for collection in collection_statements[coll]:
                col1 = 0

                worksheet.write(row - 1, col1, collection[0], wbf['header_orange'])
                col1 += 1
                worksheet.write(row - 1, col1, collection[1], wbf['header_orange'])
                col1 += 1
                worksheet.write(row - 1, col1, collection[2], wbf['header_orange'])
                col1 += 1
                worksheet.write(row - 1, col1, collection[-1], wbf['header_orange'])
                # col1 += 1
                row += 1
                sl = 1
                col3 = 0
                for product in cloumn_product:
                    column_name1 = product[0]
                    column_width = product[1]
                    column_type = product[2]
                    worksheet.set_column(col, col, column_width)
                    worksheet.write(row - 1, col3, column_name1, wbf['header_orange'])
                    # worksheet.merge_range('A2:I3', column_name, wbf['header_orange'])
                    col3 += 1
                row += 1
                picking_id = collection[4]
                query = """select sml.product_id,pt.name,sp.id,sum(sml.qty_done) from stock_picking sp 
                                           left join stock_move_line sml on sml.picking_id=sp.id
                                           left join product_product pp on pp.id=sml.product_id 
                                           left join product_template pt on pt.id= pp.product_tmpl_id 
                                           where sp.id={} group by sml.product_id,pt.name,sp.id,sml.qty_done """.format(
                    picking_id)

                self._cr.execute(query=query)
                q_result = self._cr.fetchall()
                for item in q_result:
                    col2 = 0
                    print(len(q_result))
                    print(collection[4], item[2])
                    if collection[4] == item[2]:
                        worksheet.write(row - 1, col2, sl)
                        sl += 1
                        col2 += 1
                        worksheet.write(row - 1, col2, item[1])
                        col2 += 1
                        worksheet.write(row - 1, col2, item[3])
                        col2 += 1

                        row += 1
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

        wbf['content_float'] = workbook.add_format({'align': 'right', 'num_format': '#,##0.00', 'font_name': 'Georgia'})
        wbf['content_float'].set_right()
        wbf['content_float'].set_left()

        wbf['content_number'] = workbook.add_format({'align': 'right', 'num_format': '#,##0', 'font_name': 'Georgia'})
        wbf['content_number'].set_right()
        wbf['content_number'].set_left()

        wbf['content_percent'] = workbook.add_format({'align': 'right', 'num_format': '0.00%', 'font_name': 'Georgia'})
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
            {'align': 'right', 'bg_color': colors['yellow'], 'bold': 1, 'num_format': '#,##0', 'font_name': 'Georgia'})
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
            {'align': 'right', 'bg_color': colors['orange'], 'bold': 1, 'num_format': '#,##0', 'font_name': 'Georgia'})
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
                'from_branch_id': self.from_branch_id.id, 'to_branch_id': self.to_branch_id.id
            },
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('inventory_report.stock_transfer_report').report_action(
            self, data=data)


class ReportStockTransferReportView(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.inventory_report.stock_transfer_report_view'

    # @api.model
    # def _get_report_values(self, docids, data=None):
    #     date_start = data['form']['date_start']
    #     date_end = data['form']['date_end']
    #     branch_id=data['form']['branch_id']

    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        company_id = data['form']['company_id']
        from_branch_id = data['form']['from_branch_id']
        to_branch_id = data['form']['to_branch_id']
        # branch_name = data['form']['branch_name']

        start_date = datetime.strptime(date_start, DATE_FORMAT)
        end_date = datetime.strptime(date_end, DATE_FORMAT)
        date = (end_date + relativedelta(days=+ 1))
        # e_date=end_date.date()+datetime.timedelta(days=1)

        print(date_start + "------" + date.strftime(DATETIME_FORMAT))

        if from_branch_id:
            where_from_branch_id = 'sp.location_id=%s' % from_branch_id
        else:
            where_from_branch_id = '1=1'
        if to_branch_id:
            where_to_branch_id = 'sp.location_dest_id=%s' % to_branch_id
        else:
            where_to_branch_id = '1=1'

        docs = []

        query = """
            select sp.name as reference_name,sl.complete_name as from_branch,sl1.complete_name as to_branch, sp.create_date,sp.id,sp.state from stock_picking sp 
            left join stock_location sl on sl.id=sp.location_id
            left join stock_location sl1 on sl1.id=sp.location_dest_id
            left join stock_picking_type spt on spt.id=sp.picking_type_id
            where {} and {} and  sp.date between '{}' and '{}' and sp.state = '{}' and spt.sequence_code='{}' and sp.company_id={} order by sp.create_date asc
            """.format(where_from_branch_id, where_to_branch_id, start_date.strftime(DATETIME_FORMAT),
                       date.strftime(DATETIME_FORMAT), "done", "INT", company_id)

        self._cr.execute(query=query)
        query_result = self._cr.fetchall()

        collection_statements = dict()

        for collection in query_result:
            create_date = collection[3].date()
            if create_date in collection_statements.keys():
                collection_statements[create_date].append(collection)
            else:
                collection_statements[create_date] = list()
                collection_statements[create_date].append(collection)
        print(collection_statements)
        all_product_based_move_id = []
        for get_product in query_result:
            picking_id = get_product[4]
            query = """select sml.product_id,pt.name,sp.id,sum(sml.qty_done) from stock_picking sp 

                    left join stock_move_line sml on sml.picking_id=sp.id
                    left join product_product pp on pp.id=sml.product_id 
                    left join product_template pt on pt.id= pp.product_tmpl_id 
                    where sp.id={} group by sml.product_id,pt.name,sp.id,sml.qty_done """.format(picking_id)

            self._cr.execute(query=query)
            q_result = self._cr.fetchall()
            for res in q_result:
                print(res)
                all_product_based_move_id.append(res)
        print(all_product_based_move_id)

        filtered_by_date_branch = list()
        # for collection in query_result:
        #     filtered_by_date_branch.append(collection)
        # filtered_by_date_branch1 = list(SO.search([
        #     ('date', '>=', start_date.strftime(DATETIME_FORMAT)),
        #     ('date', '<=', end_date.strftime(DATETIME_FORMAT)),
        #     # ('location_id','=',branch),
        #     ('state', 'in', ['done'])
        #
        # ]))
        total_orders = len(filtered_by_date_branch)
        # amount_total = sum(order.amount_total for order in filtered_by_date_branch)
        allsale = []
        allsale = filtered_by_date_branch
        print(allsale)

        docs.append({
            'date': start_date.strftime("%Y-%m-%d"),
            'total_orders': total_orders,
            # 'amount_total': amount_total,
            'company': self.env.user.company_id,

        })

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': start_date,
            'date_end': end_date,
            # 'docs': docs,
            'all_product_based_move_id': all_product_based_move_id,
            'collection_statements': collection_statements
            # 'grand_amount_total': amount_total,

        }