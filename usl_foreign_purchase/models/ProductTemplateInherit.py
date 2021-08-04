from odoo import api,fields, models
from datetime import date, timedelta,datetime
class ProductTemplateInherit(models.Model):
    _inherit = "product.template"

    probational_cost_ok = fields.Boolean('Is a Probational Cost', help='Indicates whether the product is a probational cost.')
    probational_percentage_ok=fields.Boolean('Is Probational Percentage', help='Indicates whether the product is probational Percentage.')
    percentage=fields.Float(string='Percentage Amount')
    probational_product = fields.One2many('probational.attribute.setup','product_probational_tmpl_id1','Product')

    @api.model_create_multi
    def create(self, vals_list):

        ''' Store the initial standard price in order to be able to retrieve the cost of a product template for a given date'''
        # for rec in self:
        if 'probational_product' in vals_list[0].keys():
            probational_products=vals_list[0].pop('probational_product')
            new_val_list=vals_list
            templates = super(ProductTemplateInherit, self).create(new_val_list)

            if "create_product_product" not in self._context:
                templates._create_variant_ids()

            # This is needed to set given values to first variant after creation
            for template, vals in zip(templates, vals_list):
                related_vals = {}
                if vals.get('barcode'):
                    related_vals['barcode'] = vals['barcode']
                if vals.get('default_code'):
                    related_vals['default_code'] = vals['default_code']
                if vals.get('standard_price'):
                    related_vals['standard_price'] = vals['standard_price']
                if vals.get('volume'):
                    related_vals['volume'] = vals['volume']
                if vals.get('weight'):
                    related_vals['weight'] = vals['weight']
                # Please do forward port
                if vals.get('packaging_ids'):
                    related_vals['packaging_ids'] = vals['packaging_ids']
                if related_vals:
                    template.write(related_vals)

            for val in probational_products:
                query = "select max(id) from probational_attribute_setup"
                self._cr.execute(query=query)
                id = self._cr.fetchone()
                max_id = 0
                if id[0] == None:
                    max_id = 1
                else:
                    max_id = id[0] + 1
                query = "insert into probational_attribute_setup " \
                        "values ({},{},{},{},{},'{}',{},'{}')".format(max_id, templates.id, val[2]['product_probational_tmpl_id'],
                                                                      val[2]['percentage'], self.env.user.id,
                                                                      str(datetime.today()), self.env.user.id,
                                                                      str(datetime.today()))
                print(query)
                self._cr.execute(query=query)

            return templates
        else:
            templates = super(ProductTemplateInherit, self).create(vals_list)

            if "create_product_product" not in self._context:
                templates._create_variant_ids()

            # This is needed to set given values to first variant after creation
            for template, vals in zip(templates, vals_list):
                related_vals = {}
                if vals.get('barcode'):
                    related_vals['barcode'] = vals['barcode']
                if vals.get('default_code'):
                    related_vals['default_code'] = vals['default_code']
                if vals.get('standard_price'):
                    related_vals['standard_price'] = vals['standard_price']
                if vals.get('volume'):
                    related_vals['volume'] = vals['volume']
                if vals.get('weight'):
                    related_vals['weight'] = vals['weight']
                # Please do forward port
                if vals.get('packaging_ids'):
                    related_vals['packaging_ids'] = vals['packaging_ids']
                if related_vals:
                    template.write(related_vals)

            return templates
    def write(self, vals):
        for rec in self:
            if 'probational_product' in vals.keys():
                for val in vals['probational_product']:
                    if val[0]==0:
                        query="select max(id) from probational_attribute_setup"
                        self._cr.execute(query=query)
                        id=self._cr.fetchone()
                        max_id = 0
                        if id[0] == None:
                            max_id = 1
                        else:
                            max_id = id[0] + 1
                        query="insert into probational_attribute_setup " \
                              "values ({},{},{},{},{},'{}',{},'{}')".format(max_id,rec.id,val[2]['product_probational_tmpl_id'],val[2]['percentage'],self.env.user.id,str(datetime.today()),self.env.user.id,str(datetime.today()))
                        print(query)
                        self._cr.execute(query=query)
                        self._cr.commit()
                        # vals.pop('probational_product')
                        #
                        # template= super(ProductTemplateInherit, self).write(vals)
                    else:
                        existing_id=val[1]
                        if val[2]:
                            if 'product_probational_tmpl_id' in val[2].keys():
                                query="update probational_attribute_setup set product_probational_tmpl_id={} where id={}".format(val[2]['product_probational_tmpl_id'],existing_id)
                                self._cr.execute(query=query)
                                self._cr.commit()
                            if 'percentage' in val[2].keys():
                                query = "update probational_attribute_setup set percentage={} where id={}".format(
                                    val[2]['percentage'], existing_id)
                                self._cr.execute(query=query)
                                self._cr.commit()
                        else:
                            query="""delete from probational_attribute_setup where id={}""".format(existing_id)
                            self._cr.execute(query=query)
                            self._cr.commit()
                            # vals.pop(self, 'probational_product')
                            # template= super(ProductTemplateInherit, self).write(vals)
                vals.pop('probational_product')
                template = super(ProductTemplateInherit, self).write(vals)

            else:
                template= super(ProductTemplateInherit, self).write(vals)
        return template



class ProbationalAttributeSetup(models.Model):
    _name = 'probational.attribute.setup'
    product_probational_tmpl_id1 = fields.Many2one('product.template',ondelete="cascade")
    product_probational_tmpl_id = fields.Many2one('product.template',ondelete="cascade" , domain=[('probational_cost_ok','=',True)])

    percentage = fields.Float(string='Percentage Amount')

    # def write(self, vals_list):
    #     print(self)
class ProductProductInherit(models.Model):
    _inherit = "product.product"

    changeable_standard_price=fields.Float()
