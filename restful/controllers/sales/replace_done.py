from odoo import http
from odoo.http import request
from .. import main
import datetime


class ReplaceProduct(http.Controller):
    @main.validate_token
    @http.route('/replace_done', auth='none', type='json', methods=['POST'], csrf=False)
    def replaceProduct(self):
        try:
            user = request.env.user
            user_id = user.id
            user_del_location = user.context_default_warehouse_id.lot_stock_id.id
            replace_name = request.jsonrequest['replace_name']
            delv_picking_type = picking_type = request.env['stock.picking.type'].search(
                [('company_id', '=', user.company_id.id), ('sequence_code', '=', 'OUT'), ('default_location_src_id', '=', user_del_location)])
            replace = request.env['product.replace'].search([('name', '=', replace_name)])

            if replace.state == 'draft':
                replace.check_availability()
                if replace.state == 'draft':
                    return {'message' : 'product not available at this moment...'}
            if replace.state == 'ready':
                location_dest_id = request.env['stock.location'].search([('name', '=', 'Customers')])
                delv_picking_vals = {  # Prepearing stock picking for delivery
                    'partner_id': replace.partner_id.id,
                    'company_id' : user.company_id.id,
                    'user_id' : user_id,
                    'picking_type_id': delv_picking_type.id,
                    'location_id': user_del_location,
                    'location_dest_id': location_dest_id.id,
                    'branch_id': user.branch_id.id,
                    'origin': replace.name,
                    'state' : 'draft',
                }
                delv_picking = request.env['stock.picking'].create(delv_picking_vals)
                # delv_picking = request.env['stock.picking'].search([('id', '=', 940)])

                for item in replace.replace_lines:
                    product = request.env['product.product'].search([('id', '=', item.product_id.id)])
                    delv_move_vals = {
                        'name': product.product_tmpl_id.name,
                        'sequence': 10,
                        'product_id': product.id,
                        'product_uom_qty': item.qty_replace,
                        'product_uom': product.product_tmpl_id.uom_id.id,
                        'location_id': user_del_location,
                        'location_dest_id': location_dest_id.id,
                        'picking_id' : delv_picking.id,
                        'origin' : replace.name
                    }
                    move = request.env['stock.move'].create(delv_move_vals)
                delv_picking.action_confirm()
                delv_picking.action_assign()
                allowed_to_validate = True
                for item in delv_picking.move_lines:
                    if item.product_uom_qty != item.reserved_availability:
                        delv_picking.do_unreserve()
                        allowed_to_validate = False
                        break

                if delv_picking.state == 'assigned' and allowed_to_validate:
                    delv_picking.button_validate()
                    transfer = request.env['stock.immediate.transfer'].search([('pick_ids', 'in', (delv_picking.id))], limit=1)
                    transfer.process()
                    replace.state = 'done'
                    if delv_picking.state != 'done':
                        backorder = request.env['stock.backorder.confirmation'].search([('pick_ids', 'in', (delv_picking.id))], limit=1)
                        backorder.process_cancel_backorder()
                else:
                    return {'message' : 'replace request stored but product not available...', 'replace' : replace.name, 'replace status' : delv_picking.state,
                            "delivery" : delv_picking.name}
            return {'message': 'replace created...', 'replace' : replace.name, 'replace status' : delv_picking.state, "delivery" : delv_picking.name, 'receive' : ""}
        except AccessError as e:
            return invalid_response("Access Error", "Error : %s" %e.name)