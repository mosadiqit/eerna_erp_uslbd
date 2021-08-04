from odoo import api, models, fields


class SaleOrderLines(models.Model):
    _inherit = 'sale.order.line'

    barcode_scan = fields.Char(string='Product Barcode', help="Here you can provide the barcode for the product")

    @api.onchange('barcode_scan')
    def _onchange_barcode_scan(self):
        product_rec = self.env['product.product']
        # product_serialno = self.env['stock_production_lot']
        # cr.execute('select * from stock_production_lot where name='+self.barcode_scan)
        # cr.fetchall()

        if self.barcode_scan:
            product = product_rec.search([('barcode', '=', self.barcode_scan)])
            if product.id == 0:
                serial = self.env["stock.production.lot"].search([('name', '=', self.barcode_scan)])
                if serial.product_id.id > 0:
                    self.product_id = serial.product_id.id
            else:
                self.product_id = product.id
            # self._cr.execute('select * from stock_production_lot where name = ' + str(self.barcode_scan))
            # for res in self.env.cr.fetchall():
            #     prod = res
            # product = product_serial.search([('name','=', self.barcode_scan)])


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
