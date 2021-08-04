from odoo import api, fields, models
from odoo import http
from odoo.http import request

class InvoicePrint(http.Controller):
    @http.route(['/invoice/print'], type='http', auth="public", website=True, sitemap=False)
    def print_saleorder(self, **kwargs):
        # sale_order_id = 2750
        # if sale_order_id:
        #     pdf, _ = request.env.ref('account.account_invoices').sudo().render_qweb_pdf([sale_order_id])
        #     pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', u'%s' % len(pdf))]
        #     return request.make_response(pdf, headers=pdfhttpheaders)
        # else:
        #     return request.redirect('/invoice'
        account = request.env['account.move'].search([('id','=',23337)])
        return request.make_response(request.env.ref('account.account_invoices').report_action(account))