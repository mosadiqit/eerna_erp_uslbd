from odoo.http import request, Response
from odoo import http
from .. import main
import datetime
from dateutil.relativedelta import *
from dateutil.parser import parse
import json

class SalesSReportas(http.Controller):
    @main.validate_token
    @http.route('/sales_summary', auth='none', type='http')
    def sales_sum_report(self, **payload):
        start_date = payload.get('start_date')
        end_date = payload.get('end_date')

        if not start_date and not end_date:
            end_date = datetime.date.today()
            start_date = end_date - relativedelta(months=+1)
        elif start_date and not end_date:
            end_date = datetime.date.today()
        elif not start_date and end_date:
            start_date = parse(end_date).date() - relativedelta(months=+1)
        current_user = request.env.user.id

        print(start_date, end_date, current_user)

        branch_id = request.env.user.branch_id.id
        company_id = request.env.user.company_id.id
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url = base_url + '/report/download?data=%5B%22%2Freport%2Fpdf%2Fsale_report.sale_summary_report_view%3Foptions%3D%257B%2522model%2522%253A%2522sale.summary.report.wizard' \
                         '%2522%252C%2522ids%2522%253A%255B7%255D%252C%2522form%2522%253A%257B%2522date_start%2522%253A%2522' + str(start_date) + \
              '%2522%252C%2522date_end%2522%253A%2522' + str(end_date) + '%2522%252C%2522company_id%2522%253A5%252C%2522branch_ids%2522%253A' + str(branch_id) + \
                                                                                  '%257D%257D%26context%3D%257B' \
                '%2522default_warehouse_id%2522%253Afalse%252C%2522lang%2522%253A%2522en_US%2522%252C%2522tz%2522%253A%2522Asia%252FDhaka%2522%252C%2522uid%2522%253A166%252C' \
                                                                                  '%2522allowed_company_ids%2522%253A%255B' \
              + str(company_id) + '%255D%252C%2522active_model%2522%253A%2522sale.summary.report.wizard%2522%252C%2522active_id%2522%253A7%252C%2522active_ids%2522%253A%255B7%255D%257D' \
                         '%22' \
                      '%2C%22qweb-pdf%22%2C%22open%22%5D&context=%7B%22default_warehouse_id%22%3Afalse%2C%22lang%22%3A%22en_US%22%2C%22tz%22%3A%22Asia%2FDhaka%22%2C%22uid%22' \
                                  '%3A166%2C%22allowed_company_ids%22%3A%5B' + str(company_id) + '%5D%7D&token=1621939381267'


        invoices = request.env['account.move'].search_count([('date', '>=', start_date), ('date', '<=', end_date), ('type', '=', 'out_invoice'), ('create_uid', '=', current_user)])
        print(invoices)
        invoices = request.env['account.move'].search([('date', '>=', start_date), ('date', '<=', end_date), ('type', '=', 'out_invoice'), ('create_uid', '=', current_user)])
        invoice_list = list()
        for invoice in invoices:
            vals = {
                'name' : invoice.name,
                'date' : str(invoice.date),
                'customer' : invoice.partner_id.id,
                'customer_name' : invoice.partner_id.name,
                'salesperson' : invoice.create_uid.id,
                'amount' : invoice.amount_total
            }
            invoice_list.append(vals)

        response = dict()
        response['status'] = True
        response['message'] = 'Successful'
        response['url'] = url
        response['invoices'] = invoice_list
        return Response(json.dumps(response), content_type='application/json;charset=utf-8', status=200)

    @main.validate_token
    @http.route('/sales_details', auth='none', type='http')
    def sales_details_report(self, **payload):
        start_date = payload.get('start_date')
        end_date = payload.get('end_date')

        if not start_date and not end_date:
            end_date = datetime.date.today()
            start_date = end_date - relativedelta(months=+1)
        elif start_date and not end_date:
            end_date = datetime.date.today()
        elif not start_date and end_date:
            start_date = parse(end_date).date() - relativedelta(months=+1)
        current_user = request.env.user.id

        print(start_date, end_date, current_user)

        uid = request.env.user.id
        branch_id = request.env.user.branch_id.id
        company_id = request.env.user.company_id.id
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url = base_url + '/report/download?data=%5B%22%2Freport%2Fpdf%2Fsale_report.daily_sales_details_report_view%3Foptions%3D%257B%2522model%2522%253A%2522daily.sales.details' \
                         '.report.wizard%2522%252C%2522ids%2522%253A%255B3%255D%252C%2522form%2522%253A%257B%2522date_start%2522%253A%2522' + str(start_date) \
              + '%2522%252C%2522date_end%2522%253A%2522' + str(end_date) + '%2522%252C%2522company_id%2522%253A5%252C%2522branch_id%2522%253Afalse%257D%257D%26context%3D%257B' \
                '%2522default_warehouse_id%2522%253Afalse%252C%2522lang%2522%253A%2522en_US%2522%252C%2522tz%2522%253A%2522Asia%252FDhaka%2522%252C%2522uid%2522%253A' + str(uid)\
              + '%252C%2522allowed_company_ids%2522%253A%255B' + str(company_id) + \
              '%255D%252C%2522active_model%2522%253A%2522daily.sales.details.report.wizard%2522%252C%2522active_id%2522%253A3' \
                '%252C%2522active_ids%2522%253A%255B3%255D%257D%22%2C%22qweb-pdf%22%2C%22open%22%5D&context=%7B%22default_warehouse_id%22%3Afalse%2C%22lang%22%3A%22en_US%22%2C' \
              '%22tz%22%3A%22Asia%2FDhaka%22%2C%22uid%22%3A166%2C%22allowed_company_ids%22%3A%5B' + str(company_id) + '%5D%7D&token=1621941223363'

        invoices = request.env['account.move'].search_count([('date', '>=', start_date), ('date', '<=', end_date), ('type', '=', 'out_invoice'), ('create_uid', '=', current_user)])
        print(invoices)
        invoices = request.env['account.move'].search([('date', '>=', start_date), ('date', '<=', end_date), ('type', '=', 'out_invoice'), ('create_uid', '=', current_user)])
        invoice_list = list()
        for invoice in invoices:
            product_list = list()
            for item in invoice.invoice_line_ids:
                move_line_vals = {
                    'product_name' : item.product_id.product_tmpl_id.name,
                    'qty' : item.quantity,
                    'price' : item.price_unit
                }
                product_list.append(move_line_vals)
            vals = {
                'name': invoice.name,
                'date': str(invoice.date),
                'customer': invoice.partner_id.id,
                'customer_name': invoice.partner_id.name,
                'customer_address': invoice.partner_id.contact_address,
                'amount': invoice.amount_total,
                'products' : product_list,
                'url' : 'adnlfnad'
            }
            invoice_list.append(vals)

        response = dict()
        response['status'] = True
        response['message'] = 'Successful'
        response['url'] = url
        response['invoices'] = invoice_list
        return Response(json.dumps(response), content_type='application/json;charset=utf-8', status=200)