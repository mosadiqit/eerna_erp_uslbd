from odoo import api, fields, models, _
from odoo.tools import float_compare


class PurchaseOrderLineInherit(models.Model):
    _inherit = 'purchase.order.line'
    _description = 'Purchase Order Line Inherit'

    # po_price=fields.Float(string='PO Price',digits=(12,4))
    # total_po = fields.Monetary(compute='_compute_total_po', string='Total PO', store=True,digits=(12,4))
    # total_os = fields.Monetary(compute='_compute_total_os',store=True,string='Total OS',digits=(12,4))
    #
    #
    # @api.depends('po_price','product_qty','price_unit')
    # def _compute_total_po(self):
    #     for line in self:
    #         print(line.product_qty)
    #         print(line.po_price)
    #         line.update({
    #             'total_po':line.product_qty*line.po_price
    #         })
    # @api.depends('total_po','price_unit')
    # def _compute_total_os(self):
    #     for line in self:
    #         if line.po_price!=0 :
    #                 line.update({
    #                  'total_os':line.total_po-(line.product_qty*line.price_unit)
    #                 })

    def _prepare_account_move_line(self, move):
        self.ensure_one()
        if self.product_id.purchase_method == 'purchase':
            qty = self.product_qty - self.qty_invoiced
        else:
            qty = self.qty_received - self.qty_invoiced
        if float_compare(qty, 0.0, precision_rounding=self.product_uom.rounding) <= 0:
            qty = 0.0

        if self.currency_id == move.company_id.currency_id:
            currency = False
        else:
            currency = move.currency_id

        return {
            'name': '%s: %s' % (self.order_id.name, self.name),
            'move_id': move.id,
            'currency_id': currency and currency.id or False,
            'purchase_line_id': self.id,
            'date_maturity': move.invoice_date_due,
            'product_uom_id': self.product_uom.id,
            'product_id': self.product_id.id,
            'price_unit': self.price_unit,
            'quantity': qty,
            'partner_id': move.partner_id.id,
            'analytic_account_id': self.account_analytic_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'display_type': self.display_type
            # 'po_price':self.po_price,
            # 'total_po':self.total_po,
            # 'total_os':self.total_os


        }




class AcoountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'
    _description = 'Account Move Line Inherit'

    po_price=fields.Float(string='PO Price' ,digits=(12,4))
    total_po = fields.Monetary(compute='_compute_total_po', string='Total PO', store=True,digits=(12,4))
    total_os = fields.Monetary(compute='_compute_total_os',store=True,string='Total OS',digits=(12,4))
    price_subtotal1=fields.Monetary(string="SubTotal",store=True,compute='_compute_sub_total')

    @api.depends('po_price', 'quantity', 'price_unit')
    def _compute_total_po(self):
        for line in self:
            line.update({
                'total_po': line.quantity * line.po_price
            })

    @api.depends('total_po', 'price_unit')
    def _compute_total_os(self):
        for line in self:
                line.update({
                    'total_os': line.total_po - (line.quantity * line.price_unit)
                })

    @api.depends('po_price','quantity', 'price_unit')
    def _compute_sub_total(self):
        for line in self:
            line.update({
                'price_subtotal1':(line.po_price+line.price_unit)*line.quantity
            })




class AcoountMoveInherit(models.Model):
    _inherit = 'account.move'
    _description = 'Account Move Inherit'

    flag = fields.Boolean(string='Flag', compute='_compute_flag')

    def _compute_flag(self):
        active_model = self.env.context.get('active_model')
        print(active_model)
        if active_model == 'purchase.order':
            self.flag=True
        else:
            self.flag=False


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'
    _description = 'Purchase Order Inherit'

    def action_view_invoice(self):
        res=super(PurchaseOrderInherit, self).action_view_invoice()
        res['context']['default_flag']=True
        return res





