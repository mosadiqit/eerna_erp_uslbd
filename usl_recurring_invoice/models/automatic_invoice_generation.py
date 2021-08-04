from datetime import date
from odoo.http import request
from odoo import api, fields, models

class AutomaticInvoiceGeneration(models.Model):
    _name = 'automatic.invoice.generation'
    # _rec_name = 'name'
    _description = 'This model will automatically create invoice with a period of time based on selected invoice.'

    def set_interval_limit(self):
        for rec in self:
            return rec.interval_limit

    def set_interval_type(self):
        for rec in self:
            return rec.interval_type


    def create_auto_invoice(self):
        print("Called")

        total_expense = 0.0
        invoice_list = self.env['automatic.invoice.generation'].search([])
        for initial in invoice_list:
            invoice_line_ids = []
            if len(invoice_list) >= 1:
                if initial.status == 'active':
                    for rec in initial.line_ids:
                        total_expense += rec.price_unit
                        val = {
                            'partner_id':rec.partner_id.id,
                            'branch_id':rec.branch_id.id,
                            'currency_id':False,
                            'debit':rec.debit,
                            'credit':rec.credit,
                            'quantity':rec.quantity,
                            'price_unit':rec.price_unit,
                            'price_subtotal':rec.price_subtotal,
                            'price_total':rec.price_total,
                            'product_id':rec.product_id.id,
                            'discount':0,
                            'sequence':10,
                            'account_id':rec.account_id.id,
                            'parent_state':'draft'
                        }
                        invoice_line_ids.append((0,0,val))
                    for rec in initial:
                        val = {
                            'partner_id':rec.customer.id,
                            'amount_total': total_expense,
                            'amount_total_signed': total_expense,
                            'branch_id': rec.write_uid.branch_id.id,
                            'notify_to_email':rec.notify_to.id,
                            'date': date.today(),
                            'journal_id': 34,
                            'currency_id': self.env.ref('base.main_company').currency_id.id,
                            'line_ids': invoice_line_ids,
                            'ref': rec.invoice.name,
                            'state': 'draft'
                        }
                        account_move = self.env['account.move']
                        account = account_move.create(val)
                        account.post()
                        self.env.ref('usl_recurring_invoice.auto_invoice_email_template').send_mail(account.id, force_send=True)
                        print("Email Sent")

                else:
                    print("No Active Invoice to auto create")
            else:
                    print("No Invoice To Create")





    @api.onchange('invoice')
    def get_product_invoice(self):
        lines = []
        line_ids_list = []
        for pre in self:
            move_id = self.env['account.move'].search([('id','=',pre.invoice.id)])
            for rec in move_id.invoice_line_ids:
                if rec.account_internal_type != 'payable':
                    vals = {
                        'product_id':rec.product_id.id,
                        'description':rec.product_id.name,
                        'quantity':rec.quantity,
                        'unit_price':rec.price_unit,
                    }
                    lines.append((0,0,vals))
            pre.invoice_line = lines
            for line in move_id.line_ids:
                vals = {
                    'account_id':line.account_id.id,
                    'branch_id':line.branch_id.id,
                    'name':line.product_id.name,
                    'debit':line.debit,
                    'credit':line.credit,
                    'price_unit':line.price_unit,
                    'quantity':line.quantity,
                    'price_total':line.price_total,
                    'price_subtotal':line.price_subtotal,
                    'partner_id':line.partner_id.id,
                    'product_id':line.product_id.id
                }
                line_ids_list.append((0, 0, vals))
            pre.line_ids = line_ids_list
    invoice = fields.Many2one('account.move',string="Invoice")
    customer = fields.Many2one('res.partner',related='invoice.partner_id',string="Customer")
    notify_to = fields.Many2one('res.users',string="Notify to")
    stop_date = fields.Date(string="Stop Date")
    invoice_line = fields.One2many('product.invoice.recurring','automatic_invoice_id')
    line_ids = fields.One2many('autoinvoice.line.ids','automatic_invoice_id')
    status = fields.Selection([
        ('active','Active'),
        ('inactive','InActive')
    ],default='active',string="Status")




class InvoiceWiseProduct(models.Model):
    _name = 'product.invoice.recurring'


    product_id = fields.Many2one('product.product',string="Product")
    description = fields.Char(related='product_id.name')
    quantity = fields.Float(string="Quantity")
    unit_price = fields.Float(string="Unit Price")
    sequence = fields.Integer(string="Sequence")
    automatic_invoice_id = fields.Many2one('automatic.invoice.generation',string="Recurring ID")



class ProductLineIds(models.Model):
    _name = 'autoinvoice.line.ids'

    currency_id = fields.Many2one('res.currency', string='Currency',
                                  required=True, readonly=True,
                                  states={'draft': [('readonly', False)]},
                                  default=lambda
                                      self: self.env.company.currency_id.id)
    automatic_invoice_id = fields.Many2one('automatic.invoice.generation', string="Recurring ID")
    account_id = fields.Many2one('account.account', string="Account ID")
    branch_id = fields.Many2one('res.branch', string="Branch")
    name = fields.Char(string="Label")
    debit = fields.Monetary(string="Debit")
    credit = fields.Monetary(string="Credit")
    price_unit = fields.Float("Price Unit")
    quantity = fields.Float(string="Quantity")
    price_total = fields.Float(string="Total Price")
    price_subtotal = fields.Float(string="Subtotal Price")
    partner_id = fields.Many2one('res.partner',string="Customer")
    product_id = fields.Many2one('product.product',string="Product")


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    notify_to_email = fields.Many2one('res.users',string="Notify to")



