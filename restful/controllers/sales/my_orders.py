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


# For Serializing the create dates
def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()


class MyOrdersAPI(http.Controller):
    @main.validate_token
    @http.route('/myOrders', auth='none', type='http')
    def fetch_my_orders(self, **payload):
        try:
            page_no = payload.get('page_no')  # '5'
            if page_no:
                page_no = int(page_no)

            limit = payload.get('limit')
            if limit:
                limit = int(limit)

            offset = 0
            if page_no and limit:
                offset = page_no * limit

            partner = int(payload.get('store_id'))
            status = str(payload.get('status'))

            logged_in = request.env.user.id
            orders = request.env['sale.order'].search([('create_uid', '=', logged_in), ('partner_id', '=', partner)], offset=offset, limit=limit)
            delivered_order_list = list()
            pending_order_list = list()
            for order in orders:
                # Check if this order is fully delivered or not
                is_partial = False
                for item in order.order_line:
                    if item.product_uom_qty != item.qty_delivered:
                        is_partial = True
                        break
                order_lines = order.order_line
                items_in_line = order_lines.product_id
                total_item_count = len(items_in_line)

                total_item_qty = 0
                total_item_price = order.amount_untaxed
                total_price_vat = order.amount_tax
                total_subtotal = order.amount_total
                total_discount = 0

                for item in order_lines:
                    total_item_qty += item.product_uom_qty
                    total_discount += item.discount

                total_total = total_subtotal - total_discount

                # Payment Infos
                payment = dict()
                invoices = order.invoice_ids.line_ids
                if not invoices:
                    payment['status'] = 'Due'
                    payment['total_paid'] = 0
                    payment['total_due'] = order.amount_total
                else:
                    for invoice in invoices:
                        if invoice.account_internal_type == 'receivable':
                            balance = invoice.balance
                            due = invoice.amount_residual
                            if due == 0:
                                payment['status'] = 'Paid'
                            else:
                                payment['status'] = 'Due'
                            payment['total_paid'] = balance - due
                            payment['total_due'] = due
                # Customer Infos
                customer = dict()
                customer['customer_name'] = order.partner_id.name if order.partner_id.name else ""
                customer['mobile_no'] = order.partner_id.mobile if order.partner_id.mobile else ""
                customer['address'] = order.partner_id.contact_address if order.partner_id.contact_address else ""

                # Delivery Infos
                all_delivery = request.env['stock.picking'].search_count(
                    [('origin', '=', order.name)])
                done_delivery = request.env['stock.picking'].search_count(
                [('origin', '=', order.name), ('state', '=', 'done')])
                order_delivered = True if all_delivery == done_delivery else False

                deliveries = request.env['stock.picking'].search([('origin', '=', order.name)])

                delivery_list = list()
                for delivery in deliveries:
                    if delivery.state == 'confirmed':
                        delivery.action_assign()
                    delivery_vals = {
                        'delivery_name' : delivery.name,
                        'delivery_status' : delivery.state
                    }
                    delivery_list.append(delivery_vals)

                # Organize Results
                vals = {
                    'order_id': order.id,
                    'order_name': order.name,
                    'is_partial' : is_partial,
                    'store_id': order.partner_id.id,
                    'total_item_count': total_item_count,
                    'total_item_quantity': total_item_qty,
                    'total_item_price': total_item_price,
                    'total_vat': total_price_vat,
                    'subtotal': total_subtotal,
                    'total_discount': total_discount,
                    'total': total_total,
                    'order_date': dumps(order.create_date, default=myconverter),
                    'payment': payment,
                    'customer': customer,
                    'delivery' : delivery_list,
                }
                if order_delivered:
                    delivered_order_list.append(vals)
                else:
                    pending_order_list.append(vals)

            response = dict()
            response['success'] = True
            response['message'] = ''
            response['orders'] = delivered_order_list if status == 'done'    else pending_order_list

            return Response(json.dumps(response), content_type='application/json;charset=utf-8', status=200)

        except AccessError as e:
            return invalid_response("Access error", "Error: %s" % e.name)