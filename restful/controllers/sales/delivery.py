from odoo.http import request
from odoo import http
from .. import main
import datetime


class DeliveryProducts(http.Controller):
    @main.validate_token
    @http.route('/delivery', auth='none', methods=['POST'], type='json', csrf=False)
    def ValidateDelivery(self):
        try:
            usr = request.env.user
            order_name = str(request.jsonrequest['order_name'])
            delivery_name = str(request.jsonrequest['delivery_name'])
            is_backorder = bool(request.jsonrequest['is_backorder'])
            products = request.jsonrequest['products']
            order = request.env['sale.order'].search([('name', '=', order_name)])
            delivery = request.env['stock.picking'].search([('name', '=', delivery_name)])
            if delivery.state == 'done':
                return {'message': 'delivery already occured'}
            # First complete the delivery and then create invoices
            else:
                if delivery.state not in ('assigned', 'done'):
                    delivery.action_assign()
                    if delivery.state != 'assigned':
                        return {'message': 'delivery is not ready due to product unavailability...'}
                if delivery.state == 'assigned':
                    moves = request.env['stock.move.line'].search([('picking_id', '=', delivery.id)])       # The delivery products lines
                    ready_product_list = list()
                    for move in moves:
                        ready_product_list.append(move.product_id.id)
                    given_p_id_list = list()       # For setting the removed products quantity zero in stock_move_line latter.
                    for product in products:  # edit the delivery according to the given product's quantity
                        p_id = int(product['id'])
                        p_qty = int(product['quantity'])
                        if p_id in ready_product_list:
                            given_p_id_list.append(p_id)
                            for move in moves:
                                if p_qty > move.product_qty and move.product_id.id == p_id:
                                    return {'message': 'Given quantity exceed...'}
                                elif move.product_id.id == p_id and p_qty <= move.product_qty and p_qty > 0:
                                    move.product_uom_qty = p_qty
                        else:
                            return {'message' : 'product with id "{}" is not ready due to product unavailability...'.format(p_id)}
                    for move in moves:
                        if move.product_id.id not in given_p_id_list:
                            move.product_uom_qty = 0
                    delivery.button_validate()
                    transfer = request.env['stock.immediate.transfer'].search([('pick_ids', 'in', (delivery.id))], limit=1)
                    transfer.process()
                    if delivery.state != 'done':  # Creating BackOrder
                        if is_backorder:
                            backorder = request.env['stock.backorder.confirmation'].search([('pick_ids', 'in', (delivery.id))], limit=1)
                            if backorder:
                                backorder.process()
                        else:
                            backorder = request.env['stock.backorder.confirmation'].search([('pick_ids', 'in', (delivery.id))], limit=1)
                            backorder.process_cancel_backorder()

                for item in delivery.move_line_ids_without_package:  # Updating qty_delivered in sale order
                    for odr_line in order.order_line:
                        if item.product_id == odr_line.product_id:
                            odr_line.qty_delivered += item.qty_done
                # Creating delivery base on the Done Delivery
                if delivery.state == 'done':
                    # Preparing price_unit_vals for invoice which contains price_unit and sale_line_id for inv_line_vals
                    price_unit_vals = dict()
                    for order_item in order.order_line:
                        price_unit_vals[order_item.product_id.id] = {'price': order_item.price_unit, 'line_id': order_item.id}
                    # Creating invoice lines
                    inv_line_list = list()
                    for delivered_item in delivery.move_line_ids_without_package:
                        print('delivered ---> ', delivered_item.product_id, delivered_item.qty_done)
                        inv_line_vals = {
                            'display_type': False,
                            'sequence': 10,
                            'name': delivered_item.product_id.product_tmpl_id.name,
                            'product_id': delivered_item.product_id.id,
                            'product_uom_id': delivered_item.product_id.product_tmpl_id.uom_id.id,
                            'quantity': delivered_item.qty_done,
                            'discount': 0.0,
                            'price_unit': price_unit_vals[delivered_item.product_id.id]['price'],
                            'tax_ids': [(6, 0, [])],
                            'analytic_account_id': False,
                            'analytic_tag_ids': [(6, 0, [])],
                            'sale_line_ids': [(4, price_unit_vals[delivered_item.product_id.id]['line_id'])]
                        }
                        inv_line_list.append((0, 0, inv_line_vals))
                    journal = request.env['account.journal'].search([('company_id', '=', usr.company_id.id), ('type', '=', 'sale'), ('code', '=', 'INV')])
                    inv_vals = {
                        'ref': '',
                        'type': 'out_invoice',
                        'currency_id': 55,
                        'campaign_id': False,
                        'medium_id': False,
                        'source_id': False,
                        'invoice_user_id': usr.id,
                        'team_id': 2,
                        'partner_id': order.partner_id.id,
                        'partner_shipping_id': order.partner_id.id,
                        'invoice_partner_bank_id': False,
                        'fiscal_position_id': False,
                        'journal_id': journal.id,
                        'invoice_origin': order.name,
                        'invoice_payment_term_id': False,
                        'invoice_payment_ref': False,
                        'transaction_ids': [(6, 0, [])],
                        'invoice_line_ids': inv_line_list,
                        'company_id': order.company_id.id,
                        'l10n_in_reseller_partner_id': False,
                        'BP_amount': 0,
                        'Security_money': 0,
                        'invoice_incoterm_id': False,
                        'branch_id': order.branch_id.id
                    }
                    inv = request.env['account.move'].create(inv_vals)
                inv.submit_for_approval()
                inv.post()
            new_backorder = request.env['stock.picking'].search([('origin', '=', order_name), ('state', '!=', 'done')], limit=1)
            if new_backorder:
                return {'message': 'Delivery Successfull...', 'backorder': new_backorder.name}
            else:
                return {'message': 'Delivery Successfull...'}
        except AccessError as e:
            return invalid_response("Access error", "Error: %s" % e.name)