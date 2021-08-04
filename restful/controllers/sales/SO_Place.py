from odoo.addons.restful.common import invalid_response, valid_response
from odoo.exceptions import AccessError
from odoo.http import request, Response
import werkzeug.wrappers
from json import dumps
from odoo import http, _
from .. import main
import datetime
import base64
import json



class PlaceOrderPostOrm(http.Controller):
    @main.validate_token
    @http.route('/placeorder_ORM', auth='none', type='json', csrf=False, methods=['POST'])
    def place_new_order(self):
        try:
            customer = int(request.jsonrequest['store_id'])
            given_products = request.jsonrequest['products']

            usr = request.env.user
            usr_team_id = request.env['crm.team']._get_default_team_id(user_id=usr.id)
            usr_location_id = int(usr.context_default_warehouse_id.lot_stock_id.id)
            journal = request.env['account.journal'].search(
                [('company_id', '=', usr.company_id.id), ('type', '=', 'sale')], limit=1)

            price_list = request.env['product.pricelist'].search(
                [('name', '=', 'Default BDT pricelist'), ('active', '=', True)])
            currency_id = price_list.currency_id.id

            product_list = []
            for given_product in given_products:
                p_id = int(given_product['id'])
                p_qty = int(given_product['quantity'])
                price = float(given_product['price'])
                line_vals = {
                    'product_id': p_id,
                    'product_uom_qty': p_qty,
                    'price_unit': price
                }
                product_list.append([0, '0', line_vals])
            vals = {
                'sale_order_template_id': False,
                'validity_date': False,
                'require_payment': False,
                'note': '',
                'user_id': usr.id,
                'company_id': usr.company_id.id,
                'require_signature': True,
                'branch_id': usr.branch_id.id,
                'warehouse_id': usr.context_default_warehouse_id.id,
                'picking_policy': 'direct',
                'partner_id': customer,
                'BP_amount': 0,
                'Security_money': 0,
                'l10n_in_reseller_partner_id': False,
                'partner_invoice_id': customer,
                'partner_shipping_id': customer,
                'pricelist_id': 2,
                'payment_term_id': False,
                'currency_id' : currency_id,
                'order_line': product_list,
                'state': 'draft',
                'cart_recovery_email_sent': False,
                'client_order_ref': False,
                'fiscal_position_id': False,
                'analytic_account_id': False,
                'l10n_in_journal_id': journal.id,
                'incoterm': False,
                'commitment_date': False,
                'origin': False,
                'opportunity_id': False,
                'campaign_id': False,
                'medium_id': False,
                'source_id': False,
                'signed_by': False,
                'signed_on': False,
                'signature': False,
                '__last_update': False,
            }
            created_order = request.env['sale.order'].create(vals)

            if created_order:
                created_order.action_confirm()
                print(created_order)
                inv = created_order._create_invoices()
                approved_inv = inv.submit_for_approval()
                posted_inv = inv.approve_invoice_order()
                print(inv)
                return {'message': 'Order created successfully...', 'order' : created_order.name}
# Payment Creation
#             paid_amount = float(request.jsonrequest['payment']['paid_amount'])
#             if paid_amount or paid_amount > 0:
#                 # print('residual = ',inv.amount_residual)
#                 # print('paid_amount = ',paid_amount)
#                 if inv.amount_residual > 0 and paid_amount <= inv.amount_residual:
#                     payment_vals = {
#                         'state' : 'draft',
#                         'payment_type' : 'inbound',
#                         'payment_method_id' : 1,
#                         'partner_type' : 'customer',
#                         'partner_id' : inv.partner_id.id,
#                         'amount' : paid_amount,
#                         'currency_id' : 55,
#                         'communication' : inv.name,
#                         'journal_id' : 54,
#                         'branch_id' : inv.branch_id.id,
#                         'invoice_ids' : inv,
#                     }
#                     payment = request.env['account.payment'].create(payment_vals)
#                     payment.post()
#                     inv._compute_payments_widget_to_reconcile_info()
#                 else:
#                     return {'message' : "Something wrong with the payment values..."}
#
#                 return {'message': 'Order created successfully...', 'order': created_order.name}
#             else:
#                 return {'message': "Order cannot be created...!"}

        except AccessError as e:
            return invalid_response("Access error", "Error: %s" % e.name)
