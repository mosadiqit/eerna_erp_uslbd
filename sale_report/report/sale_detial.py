# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo.http import request
from odoo import models, api


class Sale_DetailReport(models.AbstractModel):
    _name = 'report.sale_report.sale_detail_report_view'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        # branch_id = data['form']['branch_ids']
        # branch_name = self.env['res.branch'].search([
        #     ('id', 'in', [branch_id])
        # ]).name

        product_ids = data['form']['product_ids']
        categ_ids = data['form']['categ_ids']
        group_ids = data['form']['group_ids']
        brand_ids = data['form']['brand_ids']
        model_ids = data['form']['model_ids']
        location_ids = data['form']['location_ids']
        start_date = data['form']['date_start']
        end_date = data['form']['date_end']

        where_group_ids = " 1=1 "
        where_brand_ids = " 1=1 "
        where_model_ids = " 1=1 "
        where_branch_ids = " 1=1 "
        if categ_ids:
            product_ids = self.env['product.product'].search([('categ_id', 'in', categ_ids)])
            product_ids = [prod.id for prod in product_ids]
        where_product_ids = " 1=1 "
        where_product_ids2 = " 1=1 "
        if product_ids:
            where_product_ids = " ol.product_id in %s" % str(tuple(product_ids)).replace(',)', ')')
            where_product_ids2 = " product_id in %s" % str(tuple(product_ids)).replace(',)', ')')

        if group_ids:
            where_group_ids = " pg.id in %s" % str(tuple(group_ids)).replace(',)', ')')
        if brand_ids:
            where_brand_ids = " pb.id in %s" % str(tuple(brand_ids)).replace(',)', ')')
        if model_ids:
            where_model_ids = " pm.id in %s" % str(tuple(model_ids)).replace(',)', ')')
        if location_ids:
            where_branch_ids = " so.branch_id in %s" % str(tuple(location_ids)).replace(',)', ')')


        query = """
                    select b.name as branch, e.name as salesperson,so.name as saleorder,ac.name as invoice,p.name as buyer,pb.name as brand,pg.name as group,ol.name as product,ol.qty_invoiced,ol.price_unit,ol.price_total,ac.create_date as invoicedate,so.create_date as sodate
                    from sale_order_line as ol
                    left join sale_order as so on ol.order_id = so.id
                    left join res_partner p on so.partner_id = p.id
                    left join product_template as pt on ol.product_id = pt.id
                    left join product_group as pg on pt.group_id = pg.id
                    left join product_brand as pb on pt.brand_id = pb.id
                    left join product_model as pm on pt.product_model_id = pm.id
                    left join account_move as ac on so.name = ac.invoice_origin
                    left join hr_employee as e on so.create_uid = e.user_id
                    left join res_branch as b on so.branch_id = b.id
                    where so.invoice_status = 'invoiced' and so.create_date between '{}' and '{}' and
                        {} and {} and {} and {} and {}
                    ORDER BY 
                        sodate
                """.format(start_date, end_date, where_product_ids, where_branch_ids, where_group_ids, where_brand_ids,
                           where_model_ids)
        self._cr.execute(query)
        result = self._cr.fetchall()

        total_orders = len(result)
        amount_total = sum(order.amount_total for order in filtered_by_date)
        allsale = []
        allsale = result

        docs.append({
            'date': start_date.strftime("%Y-%m-%d"),
            'total_orders': total_orders,
            'amount_total': amount_total,
            'company': self.env.user.company_id,

        })

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': start_date,
            'date_end': end_date,
            'branch_name': branch_name,
            'docs': docs,
            'allsale': allsale,
            'grand_amount_total': amount_total,

        }




