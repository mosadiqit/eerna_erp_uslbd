from odoo import models, fields, api


class ProductWarranty(models.Model):
    _inherit = 'product.template'
    _description = 'product warranty'

    warranty = fields.Integer('Warranty', help='Product warranty by months.')
    is_lifetime_warranty = fields.Boolean('Lifetime Warranty', help='Product warranty for lifetime')
    # warranty_months = fields.Integer('Warranty (M)', help='Product warranty by Months.', compute="_compute_warranty_months")
    serial_number = fields.One2many('stock.production.lot', 'product_id_serial_number', string='Product Serial Number')
    # serial_number_values = fields.Text(string='Serial Number', compute="_compute_serial_number")

    # @api.onchange('warranty')
    # def _compute_warranty_months(self):
    #     if self.warranty:
    #         self.warranty_months = round(self.warranty / 30)

    def _compute_serial_number(self):
        print('Custom name search working!')
        product_id = self.product_variant_id.id
        print(product_id)
        serial = self.env["stock.production.lot"].search([('product_id', '=', self.product_variant_id.id)])
        new_sl = ''
        for s in serial:
            new_sl += s.name + ' '
        print(new_sl)
        self.serial_number_values = new_sl


class ProductSerialNumber(models.Model):
    _inherit = 'stock.production.lot'

    product_id_serial_number = fields.Many2one('product.template', string='Product')
