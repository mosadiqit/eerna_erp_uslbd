from odoo import api, fields, models, _

class ProductReplace(models.Model):
    _name = 'product.replace'
    _rec_name = 'name'
    _description = 'Product Replace'
    _order = 'name desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(index = True, copy=False, readonly=True, default = lambda self: _('/'))
    user_id = fields.Many2one('res.users', string='Salesman', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    recieved_wh = fields.Many2one('stock.warehouse',string='Recieved Warehouse', required=True)
    delivered_wh = fields.Many2one('stock.warehouse',string="Delivered Warehouse", required=True)
    replace_lines = fields.One2many('product.replace.lines', 'replace_id', string="Replace Lines")
    reason = fields.Text(string='Reason')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ready', 'Ready'),
        ('done', 'Done'),
        # ('return', 'Return'),
        ('cancel', 'Cancel'),
    ], readonly=True, default='draft')

    @api.model
    def create(self, valss):
        if valss.get('name', _('/') == _('/')):
            valss['name'] = self.env['ir.sequence'].next_by_code('prod.rep') or _('/')
        res = super(ProductReplace, self).create(valss)
        return res

    def check_availability(self):
        for rec in self:
            del_location = rec.delivered_wh.lot_stock_id.id
            replace_items = rec.replace_lines
            is_ready = True
            for item in replace_items:
                product = item.product_id.id
                print(product, del_location)
                qty = item.qty_replace
                stock = self.env['stock.quant'].search([('product_id', '=', product), ('location_id', '=', del_location)])
                if stock:
                    stock_avail = stock.quantity
                    stock_reserve = stock.reserved_quantity
                    stock_avail -= stock_reserve
                    if stock_avail <= 0 or item.qty_replace > stock_avail:
                        is_ready = False
                    item.qty_done = min(qty, stock_avail)

                else:
                    item.qty_done = 0
            if is_ready:
                rec.state = 'ready'

    def replace_done_action(self):
        for rec in self:
            replaces = rec.replace_lines
            for replace in replaces:
                if replace.qty_replace != replace.qty_done:
                    return
            rcv_location = rec.recieved_wh.lot_stock_id.id
            del_location = rec.delivered_wh.lot_stock_id.id
            # print(rcv_location, del_location)
            for replace in replaces:
                product = replace.product_id.id
                # print(product)
                rcv_stock = self.env['stock.quant'].search([('product_id', '=', product), ('location_id', '=', rcv_location)])
                del_stock = self.env['stock.quant'].search([('product_id', '=', product), ('location_id', '=', del_location)])
                # print(rcv_loc_qty.quantity, del_loc_qty.quantity)
                rcv_loc_qty = rcv_stock.quantity + replace.qty_done
                for i in rcv_stock:
                    i.sudo().write({'quantity' : rcv_loc_qty})

                del_loc_qty = del_stock.quantity - replace.qty_done
                for i in del_stock:
                    i.sudo().write({'quantity' : del_loc_qty})
            self.state = 'done'


    def replace_cancel_action(self):
        self.state = 'cancel'

    def replace_reset_draft_action(self):
        self.state = 'draft'

    def replace_return_action(self):
        for rec in self:
            replaces = rec.replace_lines
            rcv_location = rec.recieved_wh.lot_stock_id.id
            del_location = rec.delivered_wh.lot_stock_id.id
            # print(rcv_location, del_location)
            for replace in replaces:
                product = replace.product_id.id
                # print(product)
                rcv_stock = self.env['stock.quant'].search(
                    [('product_id', '=', product), ('location_id', '=', rcv_location)])
                del_stock = self.env['stock.quant'].search(
                    [('product_id', '=', product), ('location_id', '=', del_location)])
                # print(rcv_loc_qty.quantity, del_loc_qty.quantity)
                rcv_loc_qty = rcv_stock.quantity - replace.qty_done
                for i in rcv_stock:
                    i.sudo().write({'quantity': rcv_loc_qty})

                del_loc_qty = del_stock.quantity + replace.qty_done
                for i in del_stock:
                    i.sudo().write({'quantity': del_loc_qty})
        self.state = 'return'


class ProductReplaceLines(models.Model):
    _name = 'product.replace.lines'

    replace_id = fields.Many2one('product.replace', string="Replace ID")
    sequence = fields.Integer(string='Sequence')
    product_id = fields.Many2one('product.product', string="Product", required=True)
    qty_replace = fields.Integer(string="Qty Replace", required=True)
    qty_done = fields.Integer(string="Qty Done", readonly=True)