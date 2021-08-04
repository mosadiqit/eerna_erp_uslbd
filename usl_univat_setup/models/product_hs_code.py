
from odoo import fields, models


class OtherTaxInfo(models.Model):
    _name = 'other.tax.info'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, string="Taxes/Fees Name")
    short_name = fields.Char(required=True, string="Short Name")
    rebate_percent = fields.Float(string="Rebate Percent")
    status = fields.Selection([('1', 'Active'), ('2', 'InActive')], string="Status", default='1')
    is_fixed = fields.Boolean(string="Is Fixed")
    tax_type = fields.Selection([('1', 'Rebatable'), ('2', 'Non Rebatable'), ('3', 'N/A')], string="Tax Type", default='1')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        index=True,
        default=lambda self: self.env.company.id)


class ProductHsCode(models.Model):
    _name = 'product.hs.code'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, string="HS Code")
    business_description = fields.Char(required=True, string="Business Description")
    hs_code_line = fields.One2many('product.hs.code.line', 'hs_code_line_id', string='HS Code Lines')
    status = fields.Selection([('1', 'Active'), ('2', 'InActive')], string="Status", default='1')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        index=True,
        default=lambda self: self.env.company.id)



class ProductHSCodeLine(models.Model):
    _name = "product.hs.code.line"

    hs_code_line_id = fields.Many2one('product.hs.code', string='Other Tax Type')
    tax_type_id = fields.Many2one('product.product', string='Other Tax Type', readonly=False, domain=lambda self:self._get_product())
    assessable_rate = fields.Float(string="Assessable Rate")
    partner_id = fields.Many2one('res.partner', string='Partner')
    account_id = fields.Many2one('account.account', 'Account', domain=[('deprecated', '=', False)])


    def _get_product(self):
        query="""select pp.id from product_product pp
                left join product_template pt on pt.id=pp.product_tmpl_id where pt.landed_cost_ok=true"""
        self._cr.execute(query=query)
        product_ids=self._cr.fetchall()
        print(tuple(product_ids))
        product_id=[]
        for pid in product_ids:
            print(pid)
            product_id.append(pid[0])
        return [('id','in',tuple(product_id))]

class productTemplateHSCode(models.Model):
    _inherit = "product.template"

    product_hs_code_id = fields.Many2one('product.hs.code', string="Product HS Code")


class ResCompanyInherited(models.Model):
    _inherit = "res.company"

    vat = fields.Char(string="VAT Reg. No.")

