from odoo.addons.restful.common import invalid_response, valid_response
from odoo.exceptions import AccessError
from odoo.http import request, Response
from odoo import http, api, fields, _
from .. import main
import json
import math


class InvoiceListsAPI(http.Controller):
    @main.validate_token
    @http.route('/invoices', auth='none', type='http')
    def fetch_invoice_details(self, **payload):
        try:
            order_name = payload.get('order_name')
            if order_name:
                order_name = str(order_name)
            print('order_name = ', order_name)
            if order_name is not None:
                order = request.env['sale.order'].search([('name', '=', order_name), ('create_uid', '=', request.env.user.id)])
                if not order:
                    return Response(json.dumps({'seccess': False, 'message': 'This order does not belong to you'}),
                                    content_type='application/json;charset=utf-8', status=200)
                invoices = request.env['account.move'].search([('invoice_origin', '=', order_name)])
                outstanding_list = list()
                invoice_list = list()
                if invoices:
                    base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    # Creating outstanding list
                    for invoice in invoices:
                        if invoice.invoice_payment_state == 'not_paid':
                            choosen_inv = invoice
                            break
                        else:
                            choosen_inv = False
                    if choosen_inv:
                        inv_has_outstanding = choosen_inv.invoice_has_outstanding
                        if inv_has_outstanding:
                            info = outstanding_collection(choosen_inv)
                            print(info['content'])
                            for item in info['content']:
                                move_line = request.env['account.move.line'].search([('id', '=', int(item['id']))])
                                vals = {
                                    'id': move_line.id,
                                    'name': str(move_line.move_name),
                                    'amount': float(item['amount']),
                                    'payment_date': str(item['payment_date'])
                                }
                                outstanding_list.append(vals)
                    for invoice in invoices:
                        product_list = list()
                        for line in invoice.invoice_line_ids:
                            product_vals = {
                                'id' : line.product_id.id,
                                'name' : line.product_id.product_tmpl_id.name,
                                'quantity' : line.quantity,
                                'price' : line.price_unit,
                                'subtotal' : line.price_subtotal,
                            }
                            product_list.append(product_vals)
                        # context = request.env.ref('account.account_invoices').report_action(invoice)
                        token = '1618208488673'
                        warehs_id = str(order.create_uid.context_default_warehouse_id.id)
                        uid = str(order.create_uid.id)
                        alwd_cmpny = str(order.create_uid.company_id.id)
                        inv_id = str(invoice.id)
                        url = base_url + '/report/download?data=%5B%22%2Freport%2Fpdf%2Faccount.report_invoice_with_payments%2F' + inv_id + '%22%2C%22qweb-pdf%22%2C%22open%22%5D&context=%7B%22default_warehouse_id%22%3A' + warehs_id + '%2C%22lang%22%3A%22en_US%22%2C%22tz%22%3A%22Asia%2FDhaka%22%2C%22uid%22%3A' + uid + '%2C%22allowed_company_ids%22%3A%5B' + alwd_cmpny + '%5D%7D&token=1618194278665'
                        inv_vals = {
                            'id' : invoice.id,
                            'name' : invoice.name,
                            'state' : invoice.state,
                            'products' : product_list,
                            'total_amount' : invoice.amount_total,
                            'due_amount' : invoice.amount_residual,
                            'paid_amount' : invoice.amount_total - invoice.amount_residual,
                            'url' : url
                        }
                        invoice_list.append(inv_vals)
                response = {
                    'order_name' : order_name,
                    'invoices' : invoice_list,
                    'outstandings' : outstanding_list
                }
                return Response(json.dumps(response), content_type='application/json;charset=utf-8', status=200)
            else:
                return valid_response({'seccess': False, 'message': 'Must provide the order_name'})
        except AccessError as e:
            return invalid_response("Access error", "Error: %s" % e.name)


def outstanding_collection(self):
    for move in self:
        # move.invoice_outstanding_credits_debits_widget = json.dumps(False)
        # move.invoice_has_outstanding = False

        if move.state != 'posted' or move.invoice_payment_state != 'not_paid' or not move.is_invoice(include_receipts=True):
            continue
        pay_term_line_ids = move.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))

        domain = [('account_id', 'in', pay_term_line_ids.mapped('account_id').ids),
                  '|', ('move_id.state', '=', 'posted'), '&', ('move_id.state', '=', 'draft'), ('journal_id.post_at', '=', 'bank_rec'),
                  ('partner_id', '=', move.commercial_partner_id.id),
                  ('reconciled', '=', False), '|', ('amount_residual', '!=', 0.0),
                  ('amount_residual_currency', '!=', 0.0)]

        if move.is_inbound():
            domain.extend([('credit', '>', 0), ('debit', '=', 0)])
            type_payment = _('Outstanding credits')
        else:
            domain.extend([('credit', '=', 0), ('debit', '>', 0)])
            type_payment = _('Outstanding debits')
        info = {'title': '', 'outstanding': True, 'content': [], 'move_id': move.id}
        lines = request.env['account.move.line'].search(domain)
        currency_id = move.currency_id
        if len(lines) != 0:
            for line in lines:
                # get the outstanding residual value in invoice currency
                if line.currency_id and line.currency_id == move.currency_id:
                    amount_to_show = abs(line.amount_residual_currency)
                else:
                    currency = line.company_id.currency_id
                    amount_to_show = currency._convert(abs(line.amount_residual), move.currency_id, move.company_id,
                                                       line.date or fields.Date.today())
                if float_is_zero(amount_to_show, precision_rounding=move.currency_id.rounding):
                    continue
                info['content'].append({
                    'journal_name': line.ref or line.move_id.name,
                    'amount': amount_to_show,
                    'currency': currency_id.symbol,
                    'id': line.id,
                    'position': currency_id.position,
                    'digits': [69, move.currency_id.decimal_places],
                    'payment_date': fields.Date.to_string(line.date),
                })
            info['title'] = type_payment
            return info
            # move.invoice_outstanding_credits_debits_widget = json.dumps(info)
            # move.invoice_has_outstanding = True

def float_is_zero(value, precision_digits=None, precision_rounding=None):
    """Returns true if ``value`` is small enough to be treated as
       zero at the given precision (smaller than the corresponding *epsilon*).
       The precision (``10**-precision_digits`` or ``precision_rounding``)
       is used as the zero *epsilon*: values less than that are considered
       to be zero.
       Precision must be given by ``precision_digits`` or ``precision_rounding``,
       not both!
       Warning: ``float_is_zero(value1-value2)`` is not equivalent to
       ``float_compare(value1,value2) == 0``, as the former will round after
       computing the difference, while the latter will round before, giving
       different results for e.g. 0.006 and 0.002 at 2 digits precision.
       :param int precision_digits: number of fractional digits to round to.
       :param float precision_rounding: decimal number representing the minimum
           non-zero value at the desired precision (for example, 0.01 for a
           2-digit precision).
       :param float value: value to compare with the precision's zero
       :return: True if ``value`` is considered zero
    """
    epsilon = _float_check_precision(precision_digits=precision_digits,
                                             precision_rounding=precision_rounding)
    return abs(float_round(value, precision_rounding=epsilon)) < epsilon

def _float_check_precision(precision_digits=None, precision_rounding=None):
    assert (precision_digits is not None or precision_rounding is not None) and \
        not (precision_digits and precision_rounding),\
         "exactly one of precision_digits and precision_rounding must be specified"
    assert precision_rounding is None or precision_rounding > 0,\
         "precision_rounding must be positive, got %s" % precision_rounding
    if precision_digits is not None:
        return 10 ** -precision_digits
    return precision_rounding

def float_round(value, precision_digits=None, precision_rounding=None, rounding_method='HALF-UP'):
    """Return ``value`` rounded to ``precision_digits`` decimal digits,
       minimizing IEEE-754 floating point representation errors, and applying
       the tie-breaking rule selected with ``rounding_method``, by default
       HALF-UP (away from zero).
       Precision must be given by ``precision_digits`` or ``precision_rounding``,
       not both!
       :param float value: the value to round
       :param int precision_digits: number of fractional digits to round to.
       :param float precision_rounding: decimal number representing the minimum
           non-zero value at the desired precision (for example, 0.01 for a
           2-digit precision).
       :param rounding_method: the rounding method used: 'HALF-UP', 'UP' or 'DOWN',
           the first one rounding up to the closest number with the rule that
           number>=0.5 is rounded up to 1, the second always rounding up and the
           latest one always rounding down.
       :return: rounded float
    """
    rounding_factor = _float_check_precision(precision_digits=precision_digits,
                                             precision_rounding=precision_rounding)
    if rounding_factor == 0 or value == 0:
        return 0.0

    # NORMALIZE - ROUND - DENORMALIZE
    # In order to easily support rounding to arbitrary 'steps' (e.g. coin values),
    # we normalize the value before rounding it as an integer, and de-normalize
    # after rounding: e.g. float_round(1.3, precision_rounding=.5) == 1.5
    # Due to IEE754 float/double representation limits, the approximation of the
    # real value may be slightly below the tie limit, resulting in an error of
    # 1 unit in the last place (ulp) after rounding.
    # For example 2.675 == 2.6749999999999998.
    # To correct this, we add a very small epsilon value, scaled to the
    # the order of magnitude of the value, to tip the tie-break in the right
    # direction.
    # Credit: discussion with OpenERP community members on bug 882036

    normalized_value = value / rounding_factor # normalize
    sign = math.copysign(1.0, normalized_value)
    epsilon_magnitude = math.log(abs(normalized_value), 2)
    epsilon = 2**(epsilon_magnitude-52)

    # TIE-BREAKING: UP/DOWN (for ceiling[resp. flooring] operations)
    # When rounding the value up[resp. down], we instead subtract[resp. add] the epsilon value
    # as the the approximation of the real value may be slightly *above* the
    # tie limit, this would result in incorrectly rounding up[resp. down] to the next number
    # The math.ceil[resp. math.floor] operation is applied on the absolute value in order to
    # round "away from zero" and not "towards infinity", then the sign is
    # restored.

    if rounding_method == 'UP':
        normalized_value -= sign*epsilon
        rounded_value = math.ceil(abs(normalized_value)) * sign

    elif rounding_method == 'DOWN':
        normalized_value += sign*epsilon
        rounded_value = math.floor(abs(normalized_value)) * sign

    # TIE-BREAKING: HALF-UP (for normal rounding)
    # We want to apply HALF-UP tie-breaking rules, i.e. 0.5 rounds away from 0.
    else:
        normalized_value += math.copysign(epsilon, normalized_value)
        rounded_value = round(normalized_value)     # round to integer

    result = rounded_value * rounding_factor # de-normalize
    return result