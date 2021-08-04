from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def create(self, values):
        """Check Stock Negetive Quantity On Sale"""
        print(values)
        if 'product_id' in values and 'product_uom_qty' in values:
            location = self.env['res.users'].browse(self._context.get('uid')).context_default_warehouse_id.lot_stock_id
            self.env.cr.execute("SELECT sum(quantity) FROM stock_quant WHERE product_id=%s AND location_id=%s",
                                (values['product_id'], location.id))
            quant_st = self.env.cr.dictfetchall()
            product_obj = self.env['product.product'].browse(values['product_id'])
            qty_diff = int(product_obj.qty_available) - values['product_uom_qty']  # calcuating negative quantity
            # qty_diff = int(quant_st) - values['product_uom_qty']
            if qty_diff < 0:
                self.env['purchase.based.on.sale.order'].sudo().create(
                    {'product': product_obj.id,
                     'qty': -1 * qty_diff})  # creating a new row while clicking the save button and storing neative quantity

        return super(SaleOrderLine, self).create(values)

    def write(self, values):
        """Check Stock Negetive Quantity On Sale"""
        if 'product_uom_qty' in values:
            qty_diff = int(self.product_id.qty_available) - values['product_uom_qty']

        return super(SaleOrderLine, self).write(values)


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model_create_multi
    def create(self, vals_list):
        """Check Stock Negetive Quantity On Sale Inventory"""
        if 'move_line_ids' in vals_list[0]:
            return super(StockMove, self).create(vals_list)
        for values in vals_list:
            if 'product_uom_qty' in values and 'product_id' in values:
                location = self.env['res.users'].browse(
                    self._context.get('uid')).context_default_warehouse_id.lot_stock_id
                if not location:
                    User = self.env['res.users']
                    branch = User.search([('id', '=', self.env.user.id)])
                    warehouse_id = self.env['stock.warehouse'].sudo().search(
                        [('branch_id', '=', branch.branch_id.id)])
                    location = warehouse_id.lot_stock_id
                self.env.cr.execute("SELECT sum(quantity) FROM stock_quant WHERE product_id=%s AND location_id=%s",
                                    (values['product_id'], location.id))
                quant_st = self.env.cr.dictfetchall()
                for res in quant_st:
                    if res['sum'] == None:
                        quant_st = 0
                    else:
                        quant_st = res['sum']
                product_obj = self.env['product.product'].browse([values['product_id']])
                picking_type = self.env['stock.picking.type'].browse([values['picking_type_id']]).sequence_code
                qty_diff = int(product_obj.qty_available) - values['product_uom_qty']
                if ((values['product_uom_qty'] > int(quant_st)) and (picking_type != 'IN') and values[
                    'location_dest_id'] != 4):
                    raise ValidationError((
                                              "You cannot create delivery order because the "
                                              "stock level of the product ' %s ' and ' %s ' would become negative"
                                              " on the stock and negative stock is not allowed for this "
                                              "product and/or location.") % (
                                              product_obj.name, qty_diff))
        return super(StockMove, self).create(vals_list)

    def write(self, vals):
        """Check Stock Negetive Quantity On Sale Inventory"""
        if 'product_uom_qty' in vals:
            qty_diff = int(self.product_id.qty_available) - vals['product_uom_qty']
            if (vals['product_uom_qty'] > int(self.product_id.qty_available)) and (
                    self.picking_type_id.sequence_code != 'IN'):
                raise ValidationError((
                                          "You cannot edit delivery order because the "
                                          "stock level of the product ' %s ' is ' %s ' would become negative"
                                          " on the stock and negative stock is not allowed for this "
                                          "product and/or location.") % (
                                          self.product_id.name, qty_diff))
        return super(StockMove, self).write(vals)