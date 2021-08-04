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


class OrderDetailsAPI(http.Controller):
    @main.validate_token
    @http.route('/orderdetails', auth='none', type='http')
    def fetch_order_details(self, **payload):
        try:
            order_name = payload.get('order_name')
            if order_name:
                order_name = str(order_name)
            print('order_name = ', order_name)
            if order_name is not None:
                # Order Infos
                order = request.env['sale.order'].search([('name', '=', order_name), ('create_uid', '=', request.env.user.id)])
                if not order:
                    return Response(json.dumps({'seccess': False, 'message': 'This order does not belong to you'}),
                                    content_type='application/json;charset=utf-8', status=200)
                data = {}
                order_lines = order.order_line
                items_in_line = order_lines.product_id
                total_item_count = len(items_in_line)

                total_item_qty = 0
                total_item_price = order.amount_untaxed
                total_price_vat = order.amount_tax
                total_subtotal = 0
                total_discount = 0
                total_total = order.amount_total

                order_item_list = []
                for item in order_lines:
                    total_item_qty += item.product_uom_qty
                    total_discount += item.discount
                    total_subtotal += item.price_subtotal
                    # OrderLine Items Infos
                    vals = {
                        'product_id': item.product_id.id,
                        'product_name' : item.product_id.product_tmpl_id.name,
                        'product_unit' : item.product_id.product_tmpl_id.uom_id.name,
                        'item_count': item.product_uom_qty,
                        'ordered_quantity': item.product_uom_qty,
                        'delivered_quantity': item.qty_delivered,
                        'invoiced_quantity' : item.qty_invoiced,
                        'pending_quantity': item.product_uom_qty - item.qty_delivered,
                        'item_price': item.price_unit,
                        'vat': item.price_tax,
                        'subtotal': item.price_subtotal,
                        'discount': item.discount,
                        'total': item.price_total,
                    }
                    order_item_list.append(vals)
                # Payment Infos
                payment = dict()
                # print('order name = ',order.name)
                invoices = order.invoice_ids.line_ids
                if not invoices:
                    payment['status'] = 'Due'
                    payment['total_paid'] = 0
                    payment['total_due'] = order.amount_total
                else:
                    # print('invoices = ',invoices)
                    for invoice in invoices:
                        if invoice.account_internal_type == 'receivable':
                            balance = invoice.balance
                            due = invoice.amount_residual
                            if due == 0:
                                payment['status'] = 'Paid'
                            else:
                                payment['status'] = 'Due'
                            # print('paid = ',balance - due)
                            payment['total_paid'] = balance - due
                            payment['total_due'] = due

                # Customer_Infos
                customer = dict()
                customer['customer_name'] = order.partner_id.name if order.partner_id.name else ""
                customer['mobile_no'] = order.partner_id.mobile if order.partner_id.mobile else ""
                customer['address'] = order.partner_id.contact_address if order.partner_id.contact_address else ""

                # Delivery_Infos
                deliveries = request.env['stock.picking'].search([('origin', '=', order.name)])
                delivery_list = list()
                for delivery in deliveries:
                    delivery_vals = {
                        'delivery_name' : delivery.name,
                        'delivery_status' : delivery.state
                    }
                    delivery_list.append(delivery_vals)

                # Response Creation
                data['order_id'] = order.id
                data['order_name'] = order.name
                data['store_id'] = order.partner_id.id
                data['total_item_count'] = total_item_count
                data['total_item_quantity'] = total_item_qty
                data['total_item_price'] = total_item_price
                data['total_vat'] = total_price_vat
                data['subtotal'] = total_subtotal
                data['total_discount'] = total_discount
                data['total'] = total_total
                data['customer'] = customer
                data['payment'] = payment
                data['delivery'] = delivery_list
                data['order_items'] = order_item_list

                if data:
                    return Response(json.dumps(data), content_type='application/json;charset=utf-8', status=200)
            else:
                return valid_response({'seccess': False, 'message': 'Must provide the order_name'})
        except AccessError as e:
            return invalid_response("Access error", "Error: %s" % e.name)
