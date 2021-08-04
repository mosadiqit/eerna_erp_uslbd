from odoo import http
from odoo.http import request
from .. import main
import datetime
from odoo.exceptions import AccessError
from odoo.addons.restful.common import invalid_response



class ReplaceProductRequest(http.Controller):
    @main.validate_token
    @http.route('/replace', auth='none', type='json', methods=['POST'], csrf=False)
    def replaceProduct(self):
        try:
            user = request.env.user
            user_id = user.id
            user_del_location = user.context_default_warehouse_id.lot_stock_id.id
            customer = request.jsonrequest['store_id']
            reason = request.jsonrequest['reason']
            products = request.jsonrequest['products']
            scrap_wh = request.env['stock.warehouse'].search([('name', '=', 'Scrap Warehouse')])
            time = datetime.datetime.now()
            rcv_picking_type = request.env['stock.picking.type'].search(
                [('company_id', '=', user.company_id.id), ('sequence_code', '=', 'IN'), ('default_location_dest_id', '=', scrap_wh.lot_stock_id.id)])
            scrap_wh = request.env['stock.warehouse'].search([('name', '=', 'Scrap Warehouse')])

            product_list = list()  # Preparing replace_lines
            for product in products:
                replace_line_vals = {
                    'product_id': product['id'],
                    'sequence': 10,
                    'qty_replace': product['quantity']
                }
                product_list.append([0, '0', replace_line_vals])

            replace_vals = {  # Preparing Replace vals
                'user_id': user_id,
                'partner_id': customer,
                'recieved_wh': scrap_wh.id,
                'delivered_wh': user.context_default_warehouse_id.id,
                'replace_lines': product_list,
                'reason': reason,
                'state': 'draft'
            }
            replace = request.env['product.replace'].create(replace_vals)
            # replace = request.env['product.replace'].search([('id', '=', 19)])

            location_id = request.env['stock.location'].search([('name', '=', 'Vendors')], limit=1)
            location_dest_id = request.env['stock.location'].search([('id', '=', scrap_wh.lot_stock_id.id)])
            rcv_picking_vals = {  # Prepearing stock picking for delivery
                'partner_id': customer,
                'company_id': user.company_id.id,
                'user_id': user_id,
                'picking_type_id': rcv_picking_type.id,
                'location_id': location_id.id,
                'location_dest_id': location_dest_id.id,
                'branch_id': user.branch_id.id,
                'origin': replace.name,
                'state': 'draft',
            }
            rcv_picking = request.env['stock.picking'].create(rcv_picking_vals)

            for item in products:
                product = request.env['product.product'].search([('id', '=', int(item['id']))])
                delv_move_vals = {
                    'name': product.product_tmpl_id.name,
                    'sequence': 10,
                    'product_id': product.id,
                    'product_uom_qty': int(item['quantity']),
                    'product_uom': product.product_tmpl_id.uom_id.id,
                    'location_id': location_id.id,
                    'location_dest_id': location_dest_id.id,
                    'picking_id': rcv_picking.id,
                    'origin': replace.name
                }
                move = request.env['stock.move'].create(delv_move_vals)
            rcv_picking.action_confirm()
            rcv_picking.button_validate()
            transfer = request.env['stock.immediate.transfer'].search([('pick_ids', 'in', (rcv_picking.id))], limit=1)
            transfer.process()
            return {'message' : 'replace request placed', 'replace' : replace.name, 'WH_rcv' : rcv_picking.name}

        except AccessError as e:
            return invalid_response("Access Error", "Error : %s" %e.name)