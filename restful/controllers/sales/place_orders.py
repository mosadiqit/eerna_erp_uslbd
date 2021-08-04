from odoo.exceptions import AccessError
from odoo.http import request, Response

from odoo import http, _
from .. import main
import datetime
import pytz


class PlaceOrderQuery(http.Controller):
    @main.validate_token
    @http.route('/placeorder', auth='none', type='json', csrf=False, methods=['POST'])
    def newOrder(self):
        try:
            customer = int(request.jsonrequest['store_id'])
            products = request.jsonrequest['products']
            usr = request.env.user
            # user_loc = usr.context_default_warehouse_id.lot_stock_id.id
            time_now = datetime.datetime.now(pytz.timezone('Asia/dhaka'))
            so_name = request.env['ir.sequence'].next_by_code('sale.order', sequence_date=time_now) or _('New')
            usr_team_id = request.env['crm.team']._get_default_team_id(user_id=usr.id)
            journal = request.env['account.journal'].search([('company_id', '=', usr.company_id.id), ('type', '=', 'sale'), ('code', '=', 'INV')])

            query = '''insert into sale_order
                        (user_id, company_id, branch_id, warehouse_id, picking_policy, partner_id, name, date_order, partner_invoice_id, partner_shipping_id, pricelist_id, state, create_date, require_signature, require_payment, team_id, create_uid, write_uid, write_date, l10n_in_journal_id, invoice_status, cart_recovery_email_sent, order_made_from)
                        values ({}, 5, {}, {}, 'direct', {}, '{}', '{}', {}, {}, 2, 'sale', '{}', true, false, {}, {}, {}, '{}', {}, 'to invoice', false, 'api')'''.format(usr.id, usr.branch_id.id, usr.context_default_warehouse_id.id, customer, so_name, time_now, customer, customer, time_now, usr_team_id.id, usr.id, usr.id, time_now, journal.id)
            # print(query)
            request.cr.execute(query)
            created_order = request.env['sale.order'].search([('name', '=', so_name)])

            so_amount_untaxed = 0.0
            so_amount_tax = 0.0
            # # For creating sale_order_line
            for item in products:
                p_id = item['id']
                product = request.env['product.product'].search([('id', '=', p_id)])
                order_id = created_order.id
                name = product.product_tmpl_id.name
                price = item['price']
                qty = item['quantity']
                p_uom = product.product_tmpl_id.uom_id.id

                price_subtotal = price_total = float(price * qty)
                so_amount_untaxed += price_subtotal
                
                line_query = '''insert into sale_order_line (order_id, name, sequence, price_unit, discount, product_id, product_uom_qty, qty_delivered_method, salesman_id, company_id, state, customer_lead, create_uid, create_date, write_uid, write_date, product_uom, price_subtotal, price_tax, price_total, price_reduce, price_reduce_taxinc, price_reduce_taxexcl, invoice_status, qty_invoiced, qty_to_invoice, qty_delivered)
                values({}, '{}', 10, {}, 0.0, {}, {}, 'manual', {}, {}, 'sale', 0.0, {}, '{}', {}, '{}', {}, {}, 0, {}, 0, 0, 0, 'to invoice', 0, {}, 0)'''.format(
                    order_id, name, price, p_id, qty, usr.id, usr.company_id.id, usr.id, time_now, usr.id, time_now, p_uom,
                    price_subtotal, price_total, qty, qty)
                request.cr.execute(line_query)

            so_amount_total = so_amount_untaxed
            created_order.amount_untaxed = so_amount_untaxed
            created_order.amount_tax = so_amount_tax
            created_order.amount_total = so_amount_total

            order = request.env['sale.order'].search([('id', '=', created_order.id)])

            price_list = request.env['product.pricelist'].search(
                [('name', '=', 'Default BDT pricelist'), ('active', '=', True)])
            currency_id = price_list.currency_id.id
            order.currency_id = currency_id
            order._compute_currency_rate()
    # Delivery Creation
            usr = request.env.user
            user_loc = usr.context_default_warehouse_id.lot_stock_id.id

            procure_group_vals = {
                'partner_id': order.partner_id.id,
                'name': order.name,
                'move_type': 'direct',
                'create_uid': order.create_uid.id,
                'create_date': time_now,
                'write_uid': order.write_uid.id,
                'write_date': time_now,
                'sale_id': order.id,
                'branch_id': order.branch_id.id
            }
            procure_group = request.env['procurement.group'].create(procure_group_vals)
            print(procure_group)

            # Generating stock_picking name
            picking_type = request.env['stock.picking.type'].search(
                [('company_id', '=', order.company_id.id), ('sequence_code', '=', 'OUT'), ('default_location_src_id', '=', user_loc)])
            if picking_type.sequence_id:
                name = picking_type.sequence_id.next_by_id()
            # print('name = ', name)
            # name = 'Digit/OUT/00055'
            query = '''insert into stock_picking (branch_id, company_id, create_date, create_uid, date, group_id,immediate_transfer, is_locked, location_id, location_dest_id, move_type, name, note, origin, partner_id, picking_type_id, priority, sale_id, scheduled_date, state, user_id, write_date, write_uid)
                     values({}, {}, '{}', {}, '{}', {}, false, true, {}, 5, 'direct', '{}', '', '{}', {}, {}, 1, {}, '{}', 'confirmed', {}, '{}', {})'''.format(
                order.branch_id.id, order.company_id.id, time_now, order.create_uid.id, time_now, procure_group.id, user_loc, name,
                order.name, order.partner_id.id, picking_type.id, order.id, time_now, order.user_id.id, time_now,
                order.write_uid.id)

            request.cr.execute(query=query)
            picking = request.env['stock.picking'].search([('name', '=', name)])

            for line in order.order_line:
                p_name = line.name
                p_name = p_name.replace("'", '"')
                # print('p_name = ', p_name)
                sequence = line.sequence
                priority = picking.priority
                create_date = time_now
                date = time_now
                company_id = order.company_id.id
                date_expected = time_now
                p_id = line.product_id.id
                p_qty = p_uom_qty = line.product_uom_qty
                uom = line.product_uom.id
                location_id = picking.location_id.id
                location_dest_id = picking.location_dest_id.id
                partner = order.partner_id.id
                picking_id = picking.id
                state = 'confirmed'
                price_unit = line.price_unit
                origin = order.name
                procure_method = 'make_to_stock'
                scrapped = False
                group_id = procure_group.id
                propagate_cancel = False
                propagate_date = True
                warehouse_id = order.warehouse_id.id
                picking_type_id = picking.picking_type_id.id
                create_uid = write_uid = usr.id
                sale_line_id = line.id
                branch_id = order.branch_id.id

                stock_move_query = '''insert into stock_move (name, description_picking, sequence, priority, create_date, date, company_id, date_expected, product_id, product_qty, product_uom_qty, product_uom, location_id, location_dest_id, partner_id, picking_id, state, price_unit, origin, procure_method, scrapped, group_id, propagate_cancel, propagate_date, picking_type_id, warehouse_id, create_uid, write_uid, write_date, sale_line_id, branch_id, delay_alert, reference)
                        values('{}', '{}', {}, {}, '{}', '{}', {}, '{}', {}, {}, {}, {}, {}, {}, {}, {}, '{}', {}, '{}', '{}', {}, {}, {}, {}, {}, {}, {}, {}, '{}', {}, {}, true, '{}')'''.format(
                    p_name, p_name, sequence, priority, create_date, date, company_id, date_expected, p_id, p_qty,
                    p_uom_qty, uom, location_id, location_dest_id, partner, picking_id, state, price_unit, origin,
                    procure_method, scrapped, group_id, propagate_cancel, propagate_date, picking_type_id, warehouse_id,
                    create_uid, write_uid, time_now, sale_line_id, branch_id, picking.name)
                request.cr.execute(query=stock_move_query)
            picking.action_assign()

            # Payment
            paid_amount = float(request.jsonrequest['payment']['paid_amount'])
            if paid_amount > 0:
                journal_id = request.env['account.journal'].search(
                    [('type', '=', 'cash'), ('company_id', '=', usr.company_id.id)])
                payment_vals = {
                    'state': 'draft',
                    'payment_type': 'inbound',
                    'payment_method_id': 1,
                    'partner_type': 'customer',
                    'partner_id': order.partner_id.id,
                    'amount': paid_amount,
                    'currency_id': currency_id,
                    'communication': order.name,
                    'journal_id': journal_id.id,
                    'branch_id': order.branch_id.id,
                }
                payment = request.env['account.payment'].create(payment_vals)
                payment.submit_for_approval()
                payment.approve_custom_payment()
            return {'order': order.name, 'delivery' : picking.name}

        except AccessError as e:
            # return {''}
            return invalid_response("Access error", "Error: %s" % e.name)