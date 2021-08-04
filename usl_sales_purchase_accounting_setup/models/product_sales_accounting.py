from datetime import datetime

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare



class ProductSalesAccounting(models.Model):
    _name = "product.sale.accounting"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Product Sale Accounting Setup"

    company_id=fields.Many2one('res.company',string="Company",required=True)
    database_load=fields.Many2one('res.company',string="Company", domain=lambda self:self.get_value())
    property_cost_method=fields.Selection([
        ('standard','Standard Price'),
        ('fifo','First In First Out(FIFO)'),
        ('average','Average Cost(AVCO)')], string='Costing Metod',
        copy=False, index=True, default='average',required=True)

    property_valuation = fields.Selection([
        ('manual_periodic', 'Manual'),
        ('real_time', 'Automated')], string='Inventory Valuation',
        copy=False, index=True,default='real_time',required=True)
    income_account=fields.Many2one('all.account.account',string="Income Account",domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    income_account_int_field=fields.Integer()
    expense_account=fields.Many2one('all.account.account',string="Expense Account",domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    expense_account_int_field=fields.Integer()
    stock_input_account = fields.Many2one('all.account.account', string="Stock Input Account",
                                           domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    stock_input_account_int_field = fields.Integer()
    stock_output_account=fields.Many2one('all.account.account',string="Stock Output Account",domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    stock_output_account_int_field=fields.Integer()

    stock_valuation_account = fields.Many2one('all.account.account', string="Stock Valuation Account",
                                          domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    stock_valuation_account_int_field = fields.Integer()





    @api.model
    def create(self, vals_list):
        if 'company_id' in vals_list:
            search_company_record=self.env['product.sale.accounting'].search([('company_id','=',vals_list['company_id'])])
            if search_company_record:
                raise ValidationError(_('Account setting for this company is already exists, If you want to change settings please modify it!!!'))
                return self
        if 'income_account' in vals_list and vals_list['income_account'] > 0:
            vals_list['income_account_int_field'] = vals_list['income_account']
        if 'expense_account' in vals_list and vals_list['expense_account'] > 0:
            vals_list['expense_account_int_field'] = vals_list['expense_account']
        if 'stock_input_account' in vals_list and vals_list['stock_input_account'] > 0:
            vals_list['stock_input_account_int_field'] = vals_list['stock_input_account']
        if 'stock_output_account' in vals_list and vals_list['stock_output_account'] > 0:
            vals_list['stock_output_account_int_field'] = vals_list['stock_output_account']
        if 'stock_valuation_account' in vals_list and vals_list['stock_valuation_account'] > 0:
            vals_list['stock_valuation_account_int_field'] = vals_list['stock_valuation_account']
        return super(ProductSalesAccounting, self).create(vals_list)

    def write(self, vals):
        if 'income_account' in vals:
            if vals['income_account']>0:
                vals['income_account_int_field']=vals['income_account']
            else:
                vals['income_account_int_field']=0
        if 'expense_account' in vals:
            if vals['expense_account']>0:
                vals['expense_account_int_field']=vals['expense_account']
            else:
                vals['expense_account_int_field']=0
        if 'stock_input_account' in vals:
            if vals['stock_input_account']>0:
                vals['stock_input_account_int_field']=vals['stock_input_account']
            else:
                vals['stock_input_account_int_field']=0
        if 'stock_output_account' in vals:
            if vals['stock_output_account']>0:
                vals['stock_output_account_int_field']=vals['stock_output_account']
            else:
                vals['stock_output_account_int_field']=0
        if 'stock_valuation_account' in vals:
            if vals['stock_valuation_account']>0:
                vals['stock_valuation_account_int_field']=vals['stock_valuation_account']
            else:
                vals['stock_valuation_account_int_field']=0
        return  super(ProductSalesAccounting, self).write(vals)




    def get_value(self):
        res = self.env['account.account'].sudo().search([])
        product_sale_accounting=self.env['product.sale.accounting']
        all_account = self.env['all.account.account']

        unlink_all=self.env['all.account.account'].search([]).unlink()

        self._cr.commit()

        query="""ALTER SEQUENCE all_account_account_id_seq RESTART WITH 1"""
        self._cr.execute(query=query)
        self._cr.commit()
        all_account_array=[]
        for line in res:
            val={
                'account_account_id':line.id,
                'name':line.name,
                'code':line.code,
                'deprecated':line.deprecated,
                'user_type_id':line.user_type_id,
                'internal_type':line.internal_type,
                'internal_group':line.internal_group,
                'reconcile':line.reconcile,
                'company_id':line.company_id,
                'root_id':line.root_id,
                'create_uid':line.create_uid,
                'create_date':line.create_date,
            }
            all_account_array.append(val)
        all_account.create(all_account_array)
        self._cr.commit()
        for line in self.env['product.sale.accounting'].search([]):
            line.income_account=line.income_account_int_field if line.income_account_int_field>0 else None
            line.expense_account=line.expense_account_int_field if line.expense_account_int_field>0 else None
            line.stock_input_account = line.stock_input_account_int_field if line.stock_input_account_int_field > 0 else None
            line.stock_output_account=line.stock_output_account_int_field if line.stock_output_account_int_field>0 else None
            line.stock_valuation_account = line.stock_valuation_account_int_field if line.stock_valuation_account_int_field > 0 else None







    @api.onchange('company_id')
    def all_account(self):
        for rec in self:
            if rec.company_id.id !=False:
                print(rec.income_account)
                rec.income_account=None
                print(rec.income_account)
                return {'domain':{'income_account':[('company_id','=',rec.company_id.id)],'expense_account':[('company_id','=',rec.company_id.id)],'stock_input_account':[('company_id','=',rec.company_id.id)],'stock_output_account':[('company_id','=',rec.company_id.id)],'stock_valuation_account':[('company_id','=',rec.company_id.id)]}}

            else:
                return {'domain':{'income_account':[],'expense_account':[],'stock_input_account':[],'stock_output_account':[],'stock_valuation_account':[]}}




class AllAccounting(models.Model):
    _name = "all.account.account"


    account_account_id=fields.Integer()
    name=fields.Char(string="name")
    code=fields.Char(string="code")
    deprecated=fields.Boolean(string="deprecated")
    user_type_id=fields.Integer()
    internal_type=fields.Char()
    internal_group=fields.Char()
    reconcile=fields.Boolean()
    company_id=fields.Integer()
    root_id=fields.Integer()
    create_uid=fields.Integer()
    create_date=fields.Datetime()

    def name_get(self):
        result = []
        for rec in self:
            name = str(rec.code) + '-' + rec.name
            result.append((rec.id, name))
        return result
