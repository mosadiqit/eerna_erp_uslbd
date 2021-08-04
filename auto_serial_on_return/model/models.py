# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class StockReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"
    
    def _create_returns(self):
        res = super(StockReturnPicking, self)._create_returns()
        move_obj = self.env['stock.move.line']
        assigned_moves = self.env['stock.move']
        pick_id = self.env['stock.picking'].browse(res[0])
        for move in pick_id.mapped('move_lines').filtered(lambda x:x.state == 'assigned' and x.origin_returned_move_id and x.product_id.tracking == 'serial'):
            if len(move.origin_returned_move_id.move_line_ids) >= 1:
                move.move_line_ids.unlink()
                qty = move.product_uom_qty
                line = move.origin_returned_move_id.move_line_ids
                limit = int(self.product_return_moves.quantity)
                move_lines = self.env['stock.move.line'].search([('id','in',line.ids)], limit=limit)
                move_vals = list()
                # for i in range(int(self.product_return_moves.quantity))
                # count = 0
                for values in move_lines:
                    qty_todo = min(qty , values.qty_done)
                    vals = move._prepare_move_line_vals(qty_todo)
                    val = {'picking_id': vals['picking_id'],
                                        'product_id': vals['product_id'],
                                        'move_id':move.id,
                                        'location_id':vals[ 'location_id'],
                                        'location_dest_id':vals['location_dest_id'],
                                        'qty_done':qty_todo,
                                        'product_uom_id':vals['product_uom_id'],
                                        'lot_id':values.lot_id and values.lot_id.id or False,
                                        'lot_name':values.lot_id and values.lot_id.name or False}
                    move_vals.append(val)
                move_obj.create(move_vals)
            assigned_moves |= move
        if assigned_moves:
            assigned_moves.write({'state': 'assigned'})
        pick_id.action_assign()
        picking_val = self.env['stock.picking.type'].search(
            [('default_location_dest_id', '=', self.picking_id.location_id.id), ('is_warehouse_return', '=', True)])
        # if picking_val:
        #     list_res = list(res)
        #     list_res[1] = picking_val.id
        #     res = tuple(list_res)
        #     return res
        return res


    def create_returns(self):
        for wizard in self:
            new_picking_id, pick_type_id = wizard._create_returns()
        # Override the context to disable all the potential filters that could have been set previously
        ctx = dict(self.env.context)
        picking_val = self.env['stock.picking.type'].search(
            [('default_location_dest_id', '=', self.picking_id.location_id.id), ('is_warehouse_return', '=', True)])
        update_picking = self.env['stock.picking'].search([('id', '=', new_picking_id)])
        if picking_val:
            query = """update stock_picking set picking_type_id = {} where id = {}""".format(picking_val.id,new_picking_id)
            self._cr.execute(query=query)
            self._cr.commit()
        # if picking_val:
        #     pick_id.sudo().write({'picking_type_id': picking_val})
        ctx.update({
            'search_default_picking_type_id': pick_type_id,
            'search_default_draft': False,
            'search_default_assigned': False,
            'search_default_confirmed': False,
            'search_default_ready': False,
            'search_default_late': False,
            'search_default_available': False,
        })
        return {
            'name': _('Returned Picking'),
            'view_mode': 'form,tree,calendar',
            'res_model': 'stock.picking',
            'res_id': new_picking_id,
            'type': 'ir.actions.act_window',
            'context': ctx,
        }

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    
    return_lot_ids = fields.Many2many('stock.production.lot', compute='_get_return_lot')
    
    def _get_return_lot(self):
        for rec in self:
            returned_move_id = rec.move_id.origin_returned_move_id
            another_returned_move_id = rec.move_id.mapped('move_line_ids').mapped('lot_id')
            if returned_move_id:
                ids = []
                for line in returned_move_id.move_line_ids:
                    ids.append(line.lot_id.id)
                if ids:
                    for id in ids:
                        rec.return_lot_ids = [(4, id)]
            elif another_returned_move_id:
                rec.return_lot_ids = [(6,0, another_returned_move_id.ids)]
            else:
                ids = self.env['stock.production.lot'].search([('product_id', '=', rec.product_id.id)])
                rec.return_lot_ids = [(4, id.id) for id in ids]
