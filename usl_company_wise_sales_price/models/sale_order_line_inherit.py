from odoo import api, fields, models, _, tools
from odoo.tools.misc import formatLang, get_lang
from datetime import date,datetime
import pytz


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return
        valid_values = self.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
        # remove the is_custom values that don't belong to this template
        for pacv in self.product_custom_attribute_value_ids:
            if pacv.custom_product_template_attribute_value_id not in valid_values:
                self.product_custom_attribute_value_ids -= pacv
        # remove the no_variant attributes that don't belong to this template
        for ptav in self.product_no_variant_attribute_value_ids:
            if ptav._origin not in valid_values:
                self.product_no_variant_attribute_value_ids -= ptav
        vals = {}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = self.product_uom_qty or 1.0
        product = self.product_id.with_context(
            lang=get_lang(self.env, self.order_id.partner_id.lang).code,
            partner=self.order_id.partner_id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )
        vals.update(name=self.get_sale_order_line_multiline_description_sale(product))
        date_action = datetime.now()
        local = pytz.timezone(self.env.user.tz)
        local_dt = local.localize(date_action, is_dst=None).strftime('%Y-%m-%d %I:%M:%S')
        date_action = datetime.strptime(local_dt, '%Y-%m-%d %I:%M:%S')
        print(date_action)
        product_price_list_item = self.env['product.pricelist.item'].search(
            [('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)])

        self._compute_tax_id()
        # date_action = datetime.now().strftime('%Y-%m-%d %I:%M:%S')
        query = """SELECT id FROM product_pricelist_item where '{}' >= date_start and '{}' <= date_end and product_tmpl_id = {}""".format(
            date_action, date_action, self.product_id.product_tmpl_id.id)
        self._cr.execute(query=query)
        result = self._cr.fetchall()
        cheked_list = list()
        for i in result:
            cheked_list.append(i)
        if len(cheked_list) > 0:
            valid_product_price_list = self.env['product.pricelist.item'].search([('id', 'in', cheked_list)])
            # date_action = date.today()
            count = 0
            for val in valid_product_price_list:
                if self.product_uom_qty >= val.min_quantity:
                    if val.date_start and val.date_end and date_action >= val.date_start and date_action <= val.date_end:
                        count += 1
                    elif val.date_start and val.date_end and date_action >= val.date_start and date_action <= val.date_end or len(
                            product_price_list_item) == 1:
                        if self.product_id.product_tmpl_id.default_multi_company_price:
                            for rec in self.product_id.product_tmpl_id.default_multi_company_price:
                                if rec.company_id.id == self.env.user.company_id.id:
                                    self.write({'price_unit': rec.default_sales_price})
                        else:
                            product_template_price = self.env['product.template'].search(
                                [('id', '=', self.product_id.product_tmpl_id.id)])
                            self.write({'price_unit': product_template_price.list_price})
                    else:
                        count += 1
            if count >= 1:
                if self.order_id.pricelist_id and self.order_id.partner_id:
                    vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(
                        self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
                self.update(vals)
            else:
                if self.product_id.product_tmpl_id.default_multi_company_price:
                    for rec in self.product_id.product_tmpl_id.default_multi_company_price:
                        if rec.company_id.id == self.env.user.company_id.id:
                            vals['price_unit'] = rec.default_sales_price
                            self.update(vals)
                            # self.write({'price_unit': rec.default_sales_price})
                else:
                    product_template_price = self.env['product.template'].search(
                        [('id', '=', self.product_id.product_tmpl_id.id)])
                    vals['price_unit'] = product_template_price.list_price
                    self.update(vals)
                    # self.write({'price_unit': product_template_price.list_price})
        else:
            if self.product_id.product_tmpl_id.default_multi_company_price:
                for rec in self.product_id.product_tmpl_id.default_multi_company_price:
                    if rec.company_id.id == self.env.user.company_id.id:
                        vals['price_unit'] = rec.default_sales_price
                        self.update(vals)
            else:
                product_template_price = self.env['product.template'].search(
                    [('id', '=', self.product_id.product_tmpl_id.id)])
                vals['price_unit'] = product_template_price.list_price
                self.update(vals)
        title = False
        message = False
        result = {}
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False
        return result

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        price_list_checked = False
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        date_action = datetime.now()
        local = pytz.timezone(self.env.user.tz)
        local_dt = local.localize(date_action, is_dst=None).strftime('%Y-%m-%d %I:%M:%S')
        date_action = datetime.strptime(local_dt, '%Y-%m-%d %I:%M:%S')
        print(date_action)
        product_price_list_item = self.env['product.pricelist.item'].search(
            [('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)])
        query = """SELECT id FROM product_pricelist_item where '{}' >= date_start and '{}' <= date_end and product_tmpl_id = {}""".format(
            date_action, date_action, self.product_id.product_tmpl_id.id)
        self._cr.execute(query=query)
        result = self._cr.fetchall()
        cheked_list = list()
        for i in result:
            cheked_list.append(i)
        if len(cheked_list) > 0:
            valid_product_price_list = self.env['product.pricelist.item'].search([('id', 'in', cheked_list)])
            count = 0
            for val in valid_product_price_list:
                if self.product_uom_qty >= val.min_quantity:
                    count += 1
            if count >= 1:
                self.price_list_checked = True
                if self.order_id.pricelist_id and self.order_id.partner_id:
                    product = self.product_id.with_context(
                        lang=self.order_id.partner_id.lang,
                        partner=self.order_id.partner_id,
                        quantity=self.product_uom_qty,
                        date=self.order_id.date_order,
                        pricelist=self.order_id.pricelist_id.id,
                        uom=self.product_uom.id,
                        fiscal_position=self.env.context.get('fiscal_position')
                    )
                    self.write({'price_unit': self.env['account.tax']._fix_tax_included_price_company(
                        self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)})
            else:
                if self.product_id.product_tmpl_id.default_multi_company_price:
                    for rec in self.product_id.product_tmpl_id.default_multi_company_price:
                        if rec.company_id.id == self.env.user.company_id.id:
                            self.write({'price_unit': rec.default_sales_price})
                else:
                    product_template_price = self.env['product.template'].search(
                        [('id', '=', self.product_id.product_tmpl_id.id)])
                    self.write({'price_unit': product_template_price.list_price})
        else:
            if self.product_id.product_tmpl_id.default_multi_company_price:
                for rec in self.product_id.product_tmpl_id.default_multi_company_price:
                    if rec.company_id.id == self.env.user.company_id.id:
                        self.write({'price_unit': rec.default_sales_price})
            else:
                product_template_price = self.env['product.template'].search(
                    [('id', '=', self.product_id.product_tmpl_id.id)])
                self.write({'price_unit': product_template_price.list_price})