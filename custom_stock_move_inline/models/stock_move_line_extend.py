from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_round, float_compare


class StockMoveLineExtend(models.Model):
    _inherit = 'stock.move.line'
    _description = 'Stock_Move_Line_Extend'


    lot_id = fields.Many2one(
        'stock.production.lot', 'Lot/Serial Number',
        domain=lambda self: self._get_lot(), check_company=True)


    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        print(self.product_id)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        p_id = 0
        for a in self.product_id:
            p_id = a.id
        print(p_id)

        self._cr.execute("""select S2.LOT_ID from stock_production_lot S1
           LEft JOIN stock_move_line S2 ON S1.ID=S2.LOT_ID where S2.product_id=%s GROUP BY S2.LOT_ID having count(s2.lot_id)=1""",
                         (p_id,))
        test = self._cr.fetchall()
        # for t in test:
        res = [r[0] for r in test]
        res = {'domain': {'lot_id': [('id', 'in', res)]}}
        return res

    def _get_lot(self):
        all_lot=[]
        all_product=[]
        ctx = self.env.context
        # print(ctx.get('default_picking_id'))
        self._cr.execute('''select product_id from stock_move_line where picking_id=%s order by product_id''',
                         (ctx.get('default_picking_id'),))
        p_id = self._cr.fetchall()
        print(p_id)
        for p in p_id:
            print(p)
            self._cr.execute('''select lot_id from stock_move_line where picking_id=%s and product_id=%s''',
                         (ctx.get('default_picking_id'),p,))
            current_lot = self._cr.fetchall()
            print("current lot:",current_lot)
            self._cr.execute('''select company_id from stock_move_line where picking_id=%s''',
                             (ctx.get('default_picking_id'),))
            c_id = self._cr.fetchone()
        # # print(c_id)
            self._cr.execute("""select S2.LOT_ID from stock_production_lot S1
               LEft JOIN stock_move_line S2 ON S1.ID=S2.LOT_ID where S2.product_id=%s and S2.company_id=%s  GROUP BY S2.LOT_ID having count(s2.lot_id)=1""",
                             (p, c_id,))
            test = self._cr.fetchall()
        #     # res = [r[0] for r in test]
            print("Test:",test)
            for r in test:
                all_lot.append(r[0])
                # domain.append(('id', 'in', all_lot),('product_id','=',p))
            all_product.append(p[0])
        return [('id', 'in', all_lot)]
        # print("res:",all_lot)
        # self._cr.execute("""select * from stock_production_lot where id in %s""",(tuple(all_lot),))
        # final_result=self._cr.fetchall()
        # print("Final Result:",final_result)
        # print("Product:", self)
        #
        #
        # return [('id', 'in', all_lot),('product_id','=',self.product_id)]


    #
    # for duplicate serial validation when product return to supplier and be purchaseed
    #
    # lot_id = fields.Many2one(
    #     'stock.production.lot', 'Lot/Serial Number',
    #     domain=lambda self: self._get_lot(), check_company=True)


    # @api.onchange('lot_id')
    # def _onchange_lot_id(self):
    #     print(self.product_id)
    #
    # @api.onchange('product_id')
    # def _onchange_product_id(self):
    #     p_id = 0
    #     for a in self.product_id:
    #         p_id = a.id
    #     print(p_id)
    #
    #     self._cr.execute("""select S2.LOT_ID from stock_production_lot S1
    #        LEft JOIN stock_move_line S2 ON S1.ID=S2.LOT_ID where S2.product_id=%s GROUP BY S2.LOT_ID having count(s2.lot_id)=1""",
    #                      (p_id,))
    #     test = self._cr.fetchall()
    #     # for t in test:
    #     res = [r[0] for r in test]
    #     res = {'domain': {'lot_id': [('id', 'in', res)]}}
    #     return res
    #
    # def _get_lot(self):
    #     all_lot=[]
    #     all_product=[]
    #     ctx = self.env.context
    #     # print(ctx.get('default_picking_id'))
    #     self._cr.execute('''select product_id from stock_move_line where picking_id=%s order by product_id''',
    #                      (ctx.get('default_picking_id'),))
    #     p_id = self._cr.fetchall()
    #     print(p_id)
    #     for p in p_id:
    #         print(p)
    #         self._cr.execute('''select lot_id from stock_move_line where picking_id=%s and product_id=%s''',
    #                      (ctx.get('default_picking_id'),p,))
    #         current_lot = self._cr.fetchall()
    #         print("current lot:",current_lot)
    #         self._cr.execute('''select company_id from stock_move_line where picking_id=%s''',
    #                          (ctx.get('default_picking_id'),))
    #         c_id = self._cr.fetchone()
    #     # # print(c_id)
    #         self._cr.execute("""select S2.LOT_ID from stock_production_lot S1
    #            LEft JOIN stock_move_line S2 ON S1.ID=S2.LOT_ID where S2.product_id=%s and S2.company_id=%s  GROUP BY S2.LOT_ID having count(s2.lot_id)=1""",
    #                          (p, c_id,))
    #         test = self._cr.fetchall()
    #     #     # res = [r[0] for r in test]
    #         print("Test:",test)
    #         for r in test:
    #             all_lot.append(r[0])
    #             # domain.append(('id', 'in', all_lot),('product_id','=',p))
    #         all_product.append(p[0])
    #     return [('id', 'in', all_lot)]
    #     # print("res:",all_lot)
    #     # self._cr.execute("""select * from stock_production_lot where id in %s""",(tuple(all_lot),))
    #     # final_result=self._cr.fetchall()
    #     # print("Final Result:",final_result)
    #     # print("Product:", self)
    #     #
    #     #
    #     # return [('id', 'in', all_lot),('product_id','=',self.product_id)]

    # 
    # for duplicate serial validation when product return to supplier and be purchaseed
    #
    def _action_done(self):

        """ This method is called during a move's `action_done`. It'll actually move a quant from
        the source location to the destination location, and unreserve if needed in the source
        location.

        This method is intended to be called on all the move lines of a move. This method is not
        intended to be called when editing a `done` move (that's what the override of `write` here
        is done.
        """
        Quant = self.env['stock.quant']

        # First, we loop over all the move lines to do a preliminary check: `qty_done` should not
        # be negative and, according to the presence of a picking type or a linked inventory
        # adjustment, enforce some rules on the `lot_id` field. If `qty_done` is null, we unlink
        # the line. It is mandatory in order to free the reservation and correctly apply
        # `action_done` on the next move lines.
        ml_to_delete = self.env['stock.move.line']
        for ml in self:
            # Check here if `ml.qty_done` respects the rounding of `ml.product_uom_id`.
            uom_qty = float_round(ml.qty_done, precision_rounding=ml.product_uom_id.rounding, rounding_method='HALF-UP')
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            qty_done = float_round(ml.qty_done, precision_digits=precision_digits, rounding_method='HALF-UP')
            if float_compare(uom_qty, qty_done, precision_digits=precision_digits) != 0:
                raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
                                  defined on the unit of measure "%s". Please change the quantity done or the \
                                  rounding precision of your unit of measure.') % (ml.product_id.display_name, ml.product_uom_id.name))

            qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
            if qty_done_float_compared > 0:
                if ml.product_id.tracking != 'none':
                    picking_type_id = ml.move_id.picking_type_id
                    if picking_type_id:
                        if picking_type_id.use_create_lots:
                            # If a picking type is linked, we may have to create a production lot on
                            # the fly before assigning it to the move line if the user checked both
                            # `use_create_lots` and `use_existing_lots`.
                            if ml.lot_name and not ml.lot_id:

                                # start for inserting again of return serialn no/Lot No
                                exist_lot = self.env['stock.production.lot'].search([
                                    ('name', '=', ml.lot_name),
                                    ('product_id', '=', ml.product_id.id),
                                    ('company_id', '=', ml.move_id.company_id.id),
                                ])
                                if exist_lot:
                                    purchase_query = """
                                                        select count(id) as total_count from stock_move_line where lot_id={} and
                                                        location_id = (select id from stock_location where usage='supplier' limit 1)""".format(exist_lot.id)
                                    self._cr.execute(query=purchase_query)
                                    purchase_query_result = self._cr.fetchall()
                                    return_query = """
                                                        select count(id) as total_count from stock_move_line where lot_id={} and
                                                        location_dest_id = (select id from stock_location where usage='supplier' limit 1)""".format(exist_lot.id)
                                    self._cr.execute(query=return_query)
                                    return_query_result = self._cr.fetchall()
                                    purchase_lot_item = 0
                                    return_lot_item = 0
                                    if purchase_query_result:
                                        purchase_lot_item = purchase_query_result[0][0]

                                    if return_query_result:
                                        return_lot_item = return_query_result[0][0]

                                    if purchase_lot_item == return_lot_item:
                                        ml.write({'lot_id': exist_lot.id})
                                    else:
                                        lot = self.env['stock.production.lot'].create(
                                            {'name': ml.lot_name, 'product_id': ml.product_id.id,
                                             'company_id': ml.move_id.company_id.id}
                                        )
                                        ml.write({'lot_id': lot.id})
                                    # purchase_query = """
                                    #                         select count(id) as total_count, location_id from stock_move_line where lot_id={} and
                                    #                         location_id in (4,8) group by location_id""".format(exist_lot.id)
                                    # self._cr.execute(query=purchase_query)
                                    # purchase_query_result = self._cr.fetchall()
                                    # # return_query = """
                                    # #                             select count(id) as total_count from stock_move_line where lot_id={} and
                                    # #                             location_dest_id = (select id from stock_location where usage='supplier' limit 1)""".format(
                                    # #     exist_lot.id)
                                    # # self._cr.execute(query=return_query)
                                    # # return_query_result = self._cr.fetchall()
                                    # purchase_lot_item = 0
                                    # return_lot_item = 0
                                    # for item in purchase_query_result:
                                    #     if item[1] == 8:
                                    #         return_lot_item = item[0]
                                    #     elif item[1] == 4:
                                    #         purchase_lot_item = item[0]
                                    #
                                    # if purchase_lot_item == return_lot_item:
                                    #     ml.write({'lot_id': exist_lot.id})
                                    # else:
                                    #     lot = self.env['stock.production.lot'].create(
                                    #         {'name': ml.lot_name, 'product_id': ml.product_id.id,
                                    #          'company_id': ml.move_id.company_id.id}
                                    #     )
                                    #     ml.write({'lot_id': lot.id})

                                else:
                                    lot = self.env['stock.production.lot'].create(
                                        {'name': ml.lot_name, 'product_id': ml.product_id.id,
                                         'company_id': ml.move_id.company_id.id}
                                    )
                                    ml.write({'lot_id': lot.id})
                                # end for inserting again of return serialn no/Lot No
                                #
                                # lot = self.env['stock.production.lot'].create(
                                #     {'name': ml.lot_name, 'product_id': ml.product_id.id, 'company_id': ml.move_id.company_id.id}
                                # )
                                # ml.write({'lot_id': lot.id})
                        elif not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
                            # If the user disabled both `use_create_lots` and `use_existing_lots`
                            # checkboxes on the picking type, he's allowed to enter tracked
                            # products without a `lot_id`.
                            continue
                    elif ml.move_id.inventory_id:
                        # If an inventory adjustment is linked, the user is allowed to enter
                        # tracked products without a `lot_id`.
                        continue

                    if not ml.lot_id:
                        raise UserError(_('You need to supply a Lot/Serial number for product %s.') % ml.product_id.display_name)
            elif qty_done_float_compared < 0:
                raise UserError(_('No negative quantities allowed'))
            else:
                ml_to_delete |= ml
        ml_to_delete.unlink()

        (self - ml_to_delete)._check_company()

        # Now, we can actually move the quant.
        done_ml = self.env['stock.move.line']
        for ml in self - ml_to_delete:
            if ml.product_id.type == 'product':
                rounding = ml.product_uom_id.rounding

                # if this move line is force assigned, unreserve elsewhere if needed
                if not ml._should_bypass_reservation(ml.location_id) and float_compare(ml.qty_done, ml.product_uom_qty, precision_rounding=rounding) > 0:
                    qty_done_product_uom = ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id, rounding_method='HALF-UP')
                    extra_qty = qty_done_product_uom - ml.product_qty
                    ml._free_reservation(ml.product_id, ml.location_id, extra_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, ml_to_ignore=done_ml)
                # unreserve what's been reserved
                if not ml._should_bypass_reservation(ml.location_id) and ml.product_id.type == 'product' and ml.product_qty:
                    try:
                        Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                    except UserError:
                        Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)

                # move what's been actually done
                quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id, rounding_method='HALF-UP')
                available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                if available_qty < 0 and ml.lot_id:
                    # see if we can compensate the negative quants with some untracked quants
                    untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                    if untracked_qty:
                        taken_from_untracked_qty = min(untracked_qty, abs(quantity))
                        Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id)
                        Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id, package_id=ml.result_package_id, owner_id=ml.owner_id, in_date=in_date)
            done_ml |= ml
        # Reset the reserved quantity as we just moved it to the destination location.
        (self - ml_to_delete).with_context(bypass_reservation_update=True).write({
            'product_uom_qty': 0.00,
            'date': fields.Datetime.now(),
        })
