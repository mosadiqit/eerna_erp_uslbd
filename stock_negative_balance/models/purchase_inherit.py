from datetime import date

from odoo import models, fields, api


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        product_list2 = []
        product_set2 = set()

        for order in self:
            print(order)
            flag_document = self.env['purchase.based.on.sale.order'].sudo().search(
                [('is_purchased', '=',
                  True)])  # taking all Purchased value that is True in 'purchase.based.on.sale.order' table

            print('Flag:', flag_document)
            product_doc = self.order_line  # taking all data from order_line which is a field of purchase.order

            for doc in flag_document:
                if doc.product.id in product_set2:
                    for single_product_list in product_list2:
                        print(single_product_list)
                        if single_product_list['product_id'] == doc.product.id:
                            single_product_list['product_qty'] += doc.qty
                else:
                    product_set2.add(doc.product.id)

                    val = {
                        'product_id': doc.product.id,
                        'product_qty': doc.qty,
                    }
                    product_list2.append(val)
                    print('doc', doc)
                    print('val', val)

            for prod1 in product_doc:
                for prod in product_list2:
                    new_diff = prod['product_qty'] - prod1.product_qty  # subtracting po quantity from negative quantity
                    if prod1.product_id.id == prod['product_id'] and new_diff > 0:
                        print("yes yes")
                        self.env['purchase.based.on.sale.order'].sudo().create({'product': prod1.product_id.id,
                                                                                'qty': new_diff})
                        print('new_diff', new_diff)

            print('product_doc', product_doc)

            print('flag_document', flag_document)
            for flag in flag_document:
                flag.is_purchased = False
                print(flag.is_purchased)

            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step' \
                    or (order.company_id.po_double_validation == 'two_step' \
                        and order.amount_total < self.env.company.currency_id._convert(
                        order.company_id.po_double_validation_amount, order.currency_id, order.company_id,
                        order.date_order or fields.Date.today())) \
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
        return True

    def load_neg_stock(self):
        product_list = [(5, 0, 0)]  # Clearing previous data
        product_set = set()  # taking unique value
        for rec in self:
            document = self.env['purchase.based.on.sale.order'].sudo().search(
                [('is_purchased', '=',
                  True)])  # taking all Purchased value that is True in 'purchase.based.on.sale.order' table
            print(document)

            for doc in document:
                if doc.product.id in product_set:
                    for single_product_list in product_list[1::]:
                        print(single_product_list)
                        if single_product_list[2][
                            'product_id'] == doc.product.id:  # if product already exists in product_set then add the new quantity with previous one
                            single_product_list[2]['product_qty'] += doc.qty
                else:
                    product_set.add(doc.product.id)
                    # product_tmp = self.env['product.template'].search([('id','=',doc.product.product_tmpl_id)])
                    # print(product_tmp)
                    val = {
                        'product_id': doc.product.id,
                        'name': doc.product.product_tmpl_id.name,
                        'product_qty': doc.qty,
                        'price_unit': 0.0,
                        'order_id': rec.id,
                        'display_type': False,
                        'product_uom': doc.product.product_tmpl_id.uom_id.id,
                        'date_planned': date.today()
                    }
                    product_list.append((0, 0, val))
                    print('doc', doc)
                    print('val', val)

                rec.order_line = product_list
                print('rec.purchase_order_line', rec.order_line)
                print('product_list', product_list)
