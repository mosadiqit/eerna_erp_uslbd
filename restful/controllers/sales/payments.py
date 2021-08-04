from odoo.addons.restful.common import invalid_response, valid_response
from odoo.exceptions import AccessError
from odoo.http import request, Response
import werkzeug.wrappers
from json import dumps
from odoo import http
from .. import main
import datetime
import base64
import json


class DoPayments(http.Controller):
    @main.validate_token
    @http.route('/payments', auth='none', type='json', csrf=False, methods=['POST'])
    def paymentOfParticularOrder(self):
        try:
            order_name = request.jsonrequest['order_name']
            invoice_name = request.jsonrequest['invoice_name']
            paid_amount = request.jsonrequest['payment']['paid_amount']
            usr = request.env.user
            usr_id = usr.id
            order = request.env['sale.order'].sudo().search([('name', '=', order_name)])
            if order:
                if usr_id != order.user_id.id:
                    return Response(json.dumps({'seccess': False, 'message': 'You are not creator of this order'}),
                                    content_type='application/json;charset=utf-8', status=200)
                else:
                    if invoice_name:
                        invoice = request.env['account.move'].search([('name', '=', invoice_name)])
                        if invoice:
                            if paid_amount > 0:
                                # print('residual = ',invoice.amount_residual)
                                # print('paid_amount = ',paid_amount)
                                residual = invoice.amount_residual
                                if residual > 0 and paid_amount <= residual:
                                    journal_id = request.env['account.journal'].search(
                                        [('type', '=', 'cash'), ('company_id', '=', usr.company_id.id)])
                                    payment_vals = {
                                        'state': 'draft',
                                        'payment_type': 'inbound',
                                        'payment_method_id': 1,
                                        'partner_type': 'customer',
                                        'partner_id': invoice.partner_id.id,
                                        'amount': paid_amount,
                                        'currency_id': order.currency_id.id,
                                        'communication': invoice.name,
                                        'journal_id': journal_id.id,
                                        'branch_id': invoice.branch_id.id,
                                        'invoice_ids': invoice,
                                    }
                                    payment = request.env['account.payment'].create(payment_vals)
                                    payment.post()
                                    invoice._compute_payments_widget_to_reconcile_info()
                                    return {'message': 'Payment Successfull and added against a invoice', 'memo': payment.name}
                                else:
                                    return {'message': "Something wrong with the payment values..."}
                            else:
                                return {'message': "No paid amount provided"}
                    else:  # If there is no invoice yet
                        journal_id = request.env['account.journal'].search(
                            [('type', '=', 'cash'), ('company_id', '=', usr.company_id.id)])
                        payment_vals = {
                            'state': 'draft',
                            'payment_type': 'inbound',
                            'payment_method_id': 1,
                            'partner_type': 'customer',
                            'partner_id': order.partner_id.id,
                            'amount': paid_amount,
                            'currency_id': order.currency_id.id,
                            'communication': order.name,
                            'journal_id': journal_id.id,
                            'branch_id': order.branch_id.id,
                        }
                        payment = request.env['account.payment'].create(payment_vals)
                        payment.submit_for_approval()
                        payment.approve_custom_payment()
                        return {'message': 'Payment Successfull and added to customers outstanding', 'memo': payment.name}
            else:
                return {'message': "Order doesn't exist"}

        except AccessError as e:
            return invalid_response("Access Error", "Error : %s" % e.name)
